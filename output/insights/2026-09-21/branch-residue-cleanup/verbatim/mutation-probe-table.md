| 変異 | probe 結果 | 観測 node 数 | 観測 node (file 名省略) |
|---|---|---|---|
| m0-control-docstring-only | SURVIVED | 0 |  |
| m1-child-delete-uses-lowercase-d | MISMATCH | 7 | test_remove_child_already_clean_with_receipt, test_remove_child_archives_dirty_integrated_author_and_deletes_branch, test_remove_child_branch_delete_failure_is_partial ほか 4 |
| m2-child-delete-call-skipped | MISMATCH | 9 | test_remove_child_reflog_retained_by_other_branch, test_remove_child_already_clean_with_receipt, test_remove_child_archives_dirty_integrated_author_and_deletes_branch ほか 6 |
| m3-history-bundle-skipped | MISMATCH | 3 | test_remove_child_archives_dirty_integrated_author_and_deletes_branch, test_remove_child_bundle_verify_failure_is_partial[create], test_remove_child_bundle_verify_failure_is_partial[verify] |
| m4-integration-rejection-disabled | MISMATCH | 2 | test_remove_child_empty_owned_paths_requires_ancestry, test_remove_child_rejects_unintegrated_author_commit |
| m5-wave-delete-uses-force | MISMATCH | 27 | test_forbidden_git_verbs_absent_from_source_calls_and_runtime_allowlist, test_git_argv_spy_sees_only_allowlisted_cleanup_commands, test_accepts_arbitrary_same_uid_unreachable_process_with_diagnostics ほか 24 |
| m6-common-runner-accepts-force | MISMATCH | 1 | test_common_git_runner_rejects_force_delete |
| m7-bundle-failure-ignored | MISMATCH | 1 | test_remove_child_bundle_verify_failure_is_partial[verify] |
| m8-branch-delete-phase-mislabeled | MISMATCH | 1 | test_remove_child_branch_delete_failure_is_partial |
| m9-receipt-reappearance-check-removed | MISMATCH | 1 | test_remove_child_receipt_rejects_recreated_branch |

baseline: PASSED repo_head c82f42da712b7b46d8ea2a61c786a8d08ea3f697 spec 141384e46db8 duration_s 27.019
