## 総括

**実装済み・未実走（直接呼出し PASS／変異で赤化確認）。** pytest・正式 mutation harness は未実走です。commit は作成していません。

`remove-child` を追加しました。既存 4/5 option 形、状態 a〜e、`_parse_argv`・`_classify`・`_mutate`、既存テスト関数は維持しています。

変更ファイルと行範囲：

| ファイル | 行 |
|---|---|
| [tools/dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2778-author/tools/dev_wave_cleanup.py) | 7–8、225–238、756、988–992、1382–1794 |
| [test_dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2778-author/orchestrator/tests/test_dev_wave_cleanup.py) | 12、92–408 |
| [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2778-author/tools/check_docs.py) | 630–633 |
| [test_check_docs.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2778-author/orchestrator/tests/test_check_docs.py) | 191–194、9487、9685 |

検査結果：

- cleanup 全体の直接呼出し：**183 ケース PASS**（既存152、新設31）。capture／finalizer は代替実装を使用。
- 正例で patch・tar 復元、実 occupancy scanner、branch 保持を確認。
- メモリ上の変異 m1〜m7：全件赤化。等価変異 m0：PASS 維持。
- DW-O28 両 literal：指定本文と **996 bytes 完全一致**。
- `check_docs.py`：**rc=1、finding 1件**。親 docs 未適用による「DW-O28 の exact 契約不一致」のみ。
- `git diff --check`：PASS。

新設 node 一覧（parameter 展開後31件）：

```text
test_remove_child_archives_dirty_integrated_author_and_keeps_branch
test_remove_child_rejects_unregistered_path
test_remove_child_rejects_live_process_cwd
test_remove_child_rejects_unintegrated_author_commit
test_remove_child_empty_owned_paths_requires_ancestry
test_remove_child_rejects_nonempty_evidence_dir
test_remove_child_rejects_wave_root_and_primary
test_remove_child_rejects_branch_mismatch
test_remove_child_rejects_unreachable_reflog_history
test_remove_child_rejects_skip_worktree_flag
test_child_modes_reject_noncanonical_path
test_remove_child_admin_binding_change_is_partial
test_remove_child_already_clean_with_receipt
test_remove_child_manifest_is_closed
test_remove_child_checks_initialized_submodule
test_remove_child_detached_ancestry_and_empty_backup
```

所有外への波及は静的確認済みです。`test_pytest_collection_config.py` の既存 node、`orchestrator/test_selection_contract.py` のファイル参照、`test_branch_rescue_ledger.py` の文言参照は変更不要。共有 fixture は変更していません。親による DW-O28 本文更新が必要です。

`test_check_docs.py` の直接 import は **growth hold に拒否**されたため、解除せず未実走のままです。