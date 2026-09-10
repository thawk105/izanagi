変更箇所は [orchestrator/tests/test_acceptance_launcher.py:504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_acceptance_launcher.py:504) です。`case: str = "dup"` を `case: str` に変更しました。`parametrize`、id `dup`、恒真 assert は維持しています。

M1〜M13 の期待 node 名は全 13 件が一意に存在し、変更されていません。

- M1 `test_binding_reports_reject_extra_count`
- M2 `test_binding_report_digest_mismatch_is_rejected`
- M3 `test_binding_report_nonce_mismatch_is_rejected`
- M4 `test_binding_reports_require_exact_index_multiset[dup]`
- M5 `test_binding_enforcement_precedes_receipt`
- M6 `test_launcher_owns_k_from_environment_not_reports`
- M7 `test_unset_shard_env_fails_closed_before_runner`
- M8 `test_bound_child_executes_main_blob_not_worktree`
- M9 `test_bound_child_reports_digest_of_executed_buffer`
- M10 `test_manifest_present_adds_runner_binding_to_request`
- M11 `test_partial_manifest_environment_fails_closed`
- M12 `test_binding_applies_only_to_tests_task`
- M13 `test_binding_report_writer_output_parses_in_launcher`

対象 4 テストファイルの AST 全走査後、同型衝突は 0 件です。`git diff --check` も通過しました。git add、commit は実行していません。

## 総括

実装済み・未実走です。pytest は起動していません。  
既定値だけを外し、期待 node 名 13 件をすべて維持しました。