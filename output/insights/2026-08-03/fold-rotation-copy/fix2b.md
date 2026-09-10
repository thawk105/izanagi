`orchestrator/tests/test_spool_fold.py` のみ編集しました。docs・`tools/spool_fold.py`・`output/`・Git index/commit には触れていません。

## 総括

| 対応 | テスト名 | file:line |
|---|---|---|
| F1 | `test_rotation_can_archive_original_latest_to_fit_projected_entry` | [test_spool_fold.py:681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:681) |
| F2 | `test_completion_remaining_in_unclosed_list_relative_fences_is_rejected` | [test_spool_fold.py:924](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:924) |
| F3 正例 | `test_deferred_append_accepts_first_suffix_seen_outside_head_line_end` | [test_spool_fold.py:1013](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1013) |
| F3 replay 維持 | `test_deferred_append_rejects_replayed_identical_suffix` | [test_spool_fold.py:1335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1335) |
| F4 空 suffix | `test_empty_or_whitespace_deferred_append_suffix_is_rejected` | [test_spool_fold.py:1153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1153) |
| F4 空白 suffix | `test_whitespace_only_deferred_append_suffix_is_rejected` | [test_spool_fold.py:1161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1161) |
| F5 parse 構造・active 保存 | `test_deferred_append_only_fragment_preserves_all_active_tasks` | [test_spool_fold.py:1353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1353) |
| F5 resume 非再書込み | `test_interrupted_transaction_resumes_before_and_after_targets` | [test_spool_fold.py:768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:768) |

fix 子 A 未反映の旧実装で意図的に赤になる集合は F1・F2・F3 の新規 3 node です。F4・F5 の赤は回帰として扱います。現在の共有ツリーには子 A の修正差分も見えますが、動的な緑は主張しません。

走らせた検査:

- `git diff --check -- orchestrator/tests/test_spool_fold.py` — 成功
- `PYTHONPYCACHEPREFIX=/tmp/izanagi-fix2-test-pycache python3 -m py_compile orchestrator/tests/test_spool_fold.py` — 成功
- AST による test 名重複検査・F1〜F5 node 存在確認 — 78 test、重複なし
- pytest／plain runner／meta-test — 未実行。ホストが `pegasus02` のため、ログインノードでは実行していません

仕様の曖昧さは、F4 の「独立 node へ分割」と「既存テスト名を変更しない」の両立です。既存名は保持したまま空 suffix 専用へ絞り、空白専用 node を追加しました。

未解決項目は計算ノード上の動的実走のみです。親による対象 node、`test_plain_runner_coverage.py`、受入範囲の実行が必要です。