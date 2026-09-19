# focus3 (fix 2 巡目後、計算ノード、-n 12、8 file 同走) と段 1 (修正前、file 単独走) の比較

| file | focus3 sum s | n | fail/error/skip | 段 1 sum s | n | 差 (段1−focus3) |
|---|---|---|---|---|---|---|
| test_run_tests_preflight | 20.8 | 217 | 0/0/0 | 206.7 | 216 | +185.8 |
| test_s8b_holdout_freeze | 406.7 | 164 | 0/0/2 | — | — | — |
| test_s8b_oracle_manifest | 2.7 | 97 | 0/0/0 | — | — | — |
| test_s8b_oracle_report | 40.5 | 269 | 0/0/0 | — | — | — |
| test_s8b_ratified_freeze | 157.1 | 91 | 0/0/0 | — | — | — |
| test_s8b_ratified_verify | 223.5 | 189 | 0/0/0 | 825.3 | 189 | +601.8 |
| test_s8b_verdict | 21.4 | 65 | 0/0/0 | — | — | — |
| test_t080_freeze_migration | 69.3 | 69 | 0/0/0 | — | — | — |

## 赤 (fail/error) の node
- なし

## 修正対象 file の上位 node (この走)
### test_s8b_ratified_verify
-    8.96s (段1   15.09s) test_launch_validate_accepts_genuine_ineligible_earlier_resume
-    8.46s (段1   14.79s) test_launch_validate_rejects_genuine_eligible_earlier_official_run
-    8.40s (段1   14.61s) test_g1_selection_helper_rejects_genuine_eligible_earlier_official_run
-    8.33s (段1   14.59s) test_g1_selection_helper_accepts_genuine_ineligible_earlier_resume
-    7.55s (段1   13.45s) test_generation_two_rejected_before_artifact_io
-    7.36s (段1    7.32s) test_selector_parser_classification_boundary_at_ratified_launch
-    7.16s (段1    7.07s) test_selector_exact_exemption_accepts_declared_three_axis_evidence
-    7.01s (段1    7.09s) test_selector_payload_is_not_exempt_and_conjunction_is_scanned
-    6.96s (段1   12.93s) test_g1_only_selection_helper_skips_earlier_eligible_run_for_g2
-    6.96s (段1   12.88s) test_g1_only_selection_helper_is_noop_for_g2
-    6.68s (段1   12.70s) test_chain_g2_env_tag_unchanged_loads
-    6.52s (段1    6.43s) test_selector_launch_projection_ignores_current_choice_semantics
### test_s8b_ratified_freeze
-   19.31s (段1 —) test_emitter_memo_copy_matches_fresh_build
-   11.99s (段1 —) test_launch_rejects_invalid_v5_registry_proof[missing:freeze_sha256]
-    6.85s (段1 —) test_degraded_launch_threads_expected_use_perf_to_every_consumer
-    6.54s (段1 —) test_ratified_journal_rejects_invalid_perf_preflight_event[missing-receipt-field-perf-pref
-    6.24s (段1 —) test_launch_accepts_live_v5_registry_prefix_with_later_append
-    5.83s (段1 —) test_launch_rejects_invalid_v5_registry_proof[invalid:chain_head_sha256]
-    5.83s (段1 —) test_launch_rejects_invalid_live_v5_registry[shortened-attempt-registry-prefix-too-short]
-    5.82s (段1 —) test_launch_rejects_invalid_live_v5_registry[missing-attempt-registry-read-unavailable]
-    5.81s (段1 —) test_launch_rejects_invalid_v5_registry_proof[invalid:freeze_sha256]
-    5.79s (段1 —) test_launch_rejects_invalid_v5_registry_proof[missing:row_count]
-    5.79s (段1 —) test_launch_rejects_invalid_live_v5_registry[tampered-attempt-registry-replay-invalid]
-    5.78s (段1 —) test_launch_rejects_invalid_v5_registry_proof[invalid:protocol_sha256]
### test_run_tests_preflight
-    7.98s (段1   11.89s) test_nonacceptance_bounded_child_marker_warns_exactly_once_in_parent
-    7.95s (段1   10.79s) test_previous_full_cap_estimate_dispatches_without_local_scope
-    1.12s (段1    1.04s) test_suspect_execution_refuses_without_dispatch_or_xdist
-    1.09s (段1    1.05s) test_suspect_never_enters_local_admission
-    1.05s (段1    1.09s) test_login_headroom_import_failure_falls_back_to_dispatch
-    0.12s (段1 —) test_small_login_repo_fixture_yields_real_fingerprint
-    0.07s (段1   11.89s) test_login_local_scope_releases_budget_lease_on_infra
-    0.07s (段1   11.89s) test_login_headroom_and_queue_four_quadrants[True-True-local]
-    0.07s (段1   11.89s) test_login_non_immediate_dispatch_exempt_flags_enter_bounded_scope[--markers]
-    0.07s (段1   11.89s) test_login_non_immediate_dispatch_exempt_flags_enter_bounded_scope[--trace-config]
-    0.07s (段1   11.89s) test_login_non_immediate_dispatch_exempt_flags_enter_bounded_scope[--collect-only]
-    0.07s (段1   11.89s) test_login_headroom_and_queue_four_quadrants[False-False-local]
