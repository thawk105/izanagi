`orchestrator/tests/test_spool_fold.py` のみを編集し、25 項目を固定しました。docs・`output/`・commit 操作には触れていません。`tools/spool_fold.py` の差分は並行中の実装子 A によるものです。

## 総括

| 項目 | テスト名 | file:line |
|---:|---|---|
| 1 | `test_completion_without_remaining_field_is_rejected` | [test_spool_fold.py:792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:792) |
| 2 | `test_completion_remaining_field_rejects_noncanonical_values` | [test_spool_fold.py:805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:805) |
| 3 | `test_completion_remaining_field_rejects_duplicates` | [test_spool_fold.py:821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:821) |
| 4 | `test_completion_remaining_decoys_in_fence_and_comment_are_rejected` | [test_spool_fold.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:835) |
| 5 | `test_valid_completion_remaining_field_is_removed_from_canonical` | [test_spool_fold.py:856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:856) |
| 6 | `test_completion_base_and_remaining_trailer_order_is_independent` | [test_spool_fold.py:875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:875) |
| 7 | `test_update_and_defer_do_not_require_remaining_field` | [test_spool_fold.py:896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:896) |
| 8 | `test_n18_completion_with_remaining_work_is_rejected` | [test_spool_fold.py:776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:776) |
| 9 | `test_deferred_append_targets_single_line_item_head` | [test_spool_fold.py:914](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:914) |
| 10 | `test_deferred_append_multiline_target_preserves_continuations` | [test_spool_fold.py:925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:925) |
| 11 | `test_deferred_append_fenced_target_does_not_break_fence` | [test_spool_fold.py:944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:944) |
| 12 | `test_deferred_append_is_byte_exact_for_all_insertion_shapes` | [test_spool_fold.py:967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:967) |
| 13 | `test_empty_deferred_append_section_is_rejected` | [test_spool_fold.py:1019](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1019) |
| 14 | `test_multiline_deferred_append_item_is_rejected` | [test_spool_fold.py:1028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1028) |
| 15 | `test_empty_or_whitespace_deferred_append_suffix_is_rejected` | [test_spool_fold.py:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1040) |
| 16 | `test_deferred_append_missing_target_is_rejected` | [test_spool_fold.py:1051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1051) |
| 17 | `test_deferred_append_cannot_target_completion_record` | [test_spool_fold.py:1059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1059) |
| 18 | `test_deferred_append_rejects_visible_duplicate_target_ids` | [test_spool_fold.py:1067](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1067) |
| 19 | `test_deferred_append_ignores_comment_and_fence_decoy_items` | [test_spool_fold.py:1081](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1081) |
| 20 | `test_deferred_append_before_defer_section_is_rejected` | [test_spool_fold.py:1113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1113) |
| 21 | `test_deferred_append_can_target_item_deferred_earlier_in_same_fold` | [test_spool_fold.py:1128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1128) |
| 22 | `test_deferred_append_resolves_cross_ledger_placeholder` | [test_spool_fold.py:1155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1155) |
| 23 | `test_deferred_append_order_is_deterministic_by_fragment_key_and_item_index` | [test_spool_fold.py:1181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1181) |
| 24 | `test_deferred_append_rejects_replayed_identical_suffix` | [test_spool_fold.py:1217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1217) |
| 25 | `test_deferred_append_only_fragment_preserves_all_active_tasks` | [test_spool_fold.py:1235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1235) |

実装未投入時に期待して赤くなる集合は、表の項目 1〜6 と 9〜25、計23テストです。項目7と既存項目8は旧実装でも通るべき対照で、それ以外の赤は回帰です。

走らせた検査:

- `git diff --check -- orchestrator/tests/test_spool_fold.py` — 成功
- `python3 -m py_compile orchestrator/tests/test_spool_fold.py` — 成功（pycache は `/tmp`）
- pytest／plain runner — 走らせていません。`pegasus02` ログインノードのためです
- meta-test `test_plain_runner_coverage.py` の3 nodeid — 存在を確認しましたが、同じ理由で未実行です
- 緑は主張しません

仕様上迷った点は、`<suffix>` の先頭区切り空白を挿入 payload に含めるかです。fragment の必須空白と byte-exact 契約から、ID 直後の空白を含む substring を exact payload と解釈しました。

未解決・停止項目は動的実走のみです。親による計算ノード上の対象テスト、meta-test、受入全走が必要です。