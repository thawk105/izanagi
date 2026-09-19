# focus2 (fix 1 巡目後、計算ノード、-n 12、9 file 同走) と段 1 (修正前、file 単独走) の比較

| file | focus2 sum s | n | fail/error/skip | 段 1 sum s | n | 差 (段1−focus2) |
|---|---|---|---|---|---|---|
| test_run_tests_preflight | 17.2 | 217 | 0/0/0 | 206.7 | 216 | +189.5 |
| test_s8b_holdout_freeze | 405.5 | 164 | 0/0/2 | — | — | — |
| test_s8b_oracle_driver | 2439.3 | 158 | 0/0/6 | — | — | — |
| test_s8b_oracle_manifest | 2.5 | 97 | 0/0/0 | — | — | — |
| test_s8b_oracle_report | 40.4 | 269 | 0/0/0 | — | — | — |
| test_s8b_ratified_freeze | 165.2 | 91 | 0/0/0 | — | — | — |
| test_s8b_ratified_verify | 416.3 | 189 | 0/0/0 | 825.3 | 189 | +409.0 |
| test_s8b_verdict | 21.3 | 65 | 0/0/0 | — | — | — |
| test_t080_freeze_migration | 69.7 | 69 | 0/0/0 | — | — | — |

## 赤 (fail/error) の node
- なし

## 修正対象 file の上位 node (この走)
### test_s8b_ratified_verify
-   14.10s (段1   13.73s) test_frozen_at_head_not_generation_parent_rejected
-   14.10s (段1   13.49s) test_valid_session_requires_run_cmd_even_when_journal_and_result_agree
-   14.10s (段1   13.68s) test_env_tag_unknown_rejected
-   14.04s (段1   13.53s) test_transition_out_of_enumeration_diff_rejected[<lambda>4]
-   13.97s (段1   13.35s) test_portable_binary_coherent_island_rejected_by_exact_cause[binding-sha]
-   13.94s (段1   13.48s) test_closure_entry_absent_from_generation_tree_rejected
-   13.87s (段1   13.71s) test_transition_out_of_enumeration_diff_rejected[<lambda>2]
-   13.71s (段1   13.74s) test_transition_out_of_enumeration_diff_rejected[<lambda>3]
-   13.68s (段1   13.80s) test_transition_out_of_enumeration_diff_rejected[<lambda>0]
-   13.62s (段1   13.35s) test_portable_binary_coherent_island_rejected_by_exact_cause[binary-cell-binding]
-   13.56s (段1   13.60s) test_source_blob_mismatch_rejected
-   13.55s (段1   13.37s) test_portable_binary_coherent_island_rejected_by_exact_cause[binaries-cell-set]
### test_s8b_ratified_freeze
-   20.09s (段1 —) test_emitter_memo_copy_matches_fresh_build
-   14.00s (段1 —) test_production_emitter_staged_builder_is_git_deterministic_across_roots
-   12.13s (段1 —) test_launch_rejects_invalid_v5_registry_proof[missing:freeze_sha256]
-    7.11s (段1 —) test_degraded_launch_threads_expected_use_perf_to_every_consumer
-    6.31s (段1 —) test_launch_accepts_live_v5_registry_prefix_with_later_append
-    6.17s (段1 —) test_launch_rejects_invalid_live_v5_registry[tampered-attempt-registry-replay-invalid]
-    6.15s (段1 —) test_launch_rejects_invalid_v5_registry_proof[invalid:chain_head_sha256]
-    6.04s (段1 —) test_launch_rejects_invalid_v5_registry_proof[missing:schema]
-    5.85s (段1 —) test_launch_rejects_invalid_v5_registry_proof[invalid:row_count]
-    5.82s (段1 —) test_launch_rejects_invalid_v5_registry_proof[invalid:registry_schema]
-    5.81s (段1 —) test_launch_rejects_invalid_v5_registry_proof[extra-key]
-    5.81s (段1 —) test_launch_rejects_invalid_v5_registry_proof[missing:protocol_sha256]
### test_run_tests_preflight
-    6.87s (段1   11.89s) test_nonacceptance_bounded_child_marker_warns_exactly_once_in_parent
-    5.49s (段1   10.79s) test_previous_full_cap_estimate_dispatches_without_local_scope
-    1.09s (段1    1.04s) test_suspect_execution_refuses_without_dispatch_or_xdist
-    1.09s (段1    1.05s) test_suspect_never_enters_local_admission
-    1.06s (段1    1.09s) test_login_headroom_import_failure_falls_back_to_dispatch
-    0.12s (段1 —) test_small_login_repo_fixture_yields_real_fingerprint
-    0.07s (段1    8.27s) test_login_collect_only_from_pytest_addopts_enters_bounded_scope
-    0.07s (段1   11.90s) test_without_force_dispatch_login_with_headroom_still_runs_local
-    0.06s (段1    8.26s) test_login_local_scope_releases_budget_lease_on_interrupt
-    0.06s (段1   11.88s) test_login_headroom_and_queue_four_quadrants[True-False-local]
-    0.06s (段1   11.89s) test_login_headroom_and_queue_four_quadrants[False-False-local]
-    0.06s (段1   11.89s) test_local_child_test_failure_never_falls_back
