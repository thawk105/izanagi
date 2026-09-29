## 総括

**実装済み・未実走です。** 子木の退避撤去、main 前進の許容、子 branch の compare-and-delete、DW-O28 の pin 更新を行いました。Stop hook は作成できず、配線も未実施です。commit はしていません。

## 変更一覧

- [tools/dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/tools/dev_wave_cleanup.py:1618): 退避経路の条件、main 祖先判定、期待 old OID 付き branch 削除、receipt と stderr の basis を追加。
- [orchestrator/tests/test_dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/orchestrator/tests/test_dev_wave_cleanup.py:335): 許可された正例への変更と、wave・ref・detached・main 巻戻し・branch 競合の負例を追加。
- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/tools/check_docs.py:631)、[orchestrator/tests/test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/orchestrator/tests/test_check_docs.py:189): DW-O28 の現行本文に一致させ、996 bytes に更新。

## 現行挙動と変更後挙動

従来は未統合の子 commit と空の `owned_paths` を拒否し、proof 後の main tip 変更も拒否していました。変更後は裁定の退避条件を満たす子を撤去対象とし、proof 時 tip が現 main の祖先なら続行します。子 branch は `update-ref -d` に期待 old OID を渡します。

## テスト実走

指定した cleanup の 4 nodeid は**未実走**です。`tools/run_tests.py` の Pegasus dispatch が `qstat -Q` 事前確認で rc=16 となりました。変更した Python 4 ファイルの構文検査と `git diff --check` は通過しました。DW-O28 の本文と両 pin は 996 bytes で一致し、指定変異は 999 bytes です。

`python3 tools/check_docs.py` は `docs/dev-wave/**` の予算超過（9723/9696 bytes）で赤でした。

## 変異 M1〜M12 の対応 test

| 変異 | 対応 |
|---|---|
| M1 | `test_remove_child_archive_requires_landed_wave` |
| M2 | 既存 `test_remove_child_rejects_unreachable_reflog_history` |
| M3 | `test_remove_child_archive_rejects_private_worktree_ref` |
| M4 | `test_remove_child_archive_rejects_detached_nonancestor` |
| M5 | 更新した `test_remove_child_rejects_unintegrated_author_commit` |
| M6 | `test_remove_child_main_rewind_during_removal_is_partial` |
| M7 | `test_remove_child_main_advance_during_removal_completes` |
| M8 | `test_remove_child_branch_compare_delete_preserves_moved_ref` |
| M9〜M12 | Stop hook・配線が未実装のため未対応 |

いずれも変異実走による単一理由性は未確認です。

## 波及の静的列挙

`test_branch_rescue_ledger.py` と `test_check_branch_rescue.py` は DW-O28 に言及しますが、今回の cleanup 呼出しは見つかりませんでした。`test_pytest_collection_config.py` は test file 集合を列挙します。指定の inventory 系 4 群を含め、制約 meta-test は未実走です。

## 未了・リスク

`hooks/guard_dev_wave_cleanup_stop.py` の作成は PreToolUse の `guard_write` が **`hooks/` への直接書き込み**として拒否しました。このため `.claude/settings.json` に動作しない Stop 配線は追加していません。

既存の `branch -D` 呼出しを固定するテスト 2 本は compare-and-delete と衝突しますが、裁定が許す期待値変更の閉集合外なので変更していません。テスト未実走のため、cleanup の完成・緑は主張できません。揮発値を期待値へ固定する変更は加えていませんが、揮発源を変えた再走も未実施です。