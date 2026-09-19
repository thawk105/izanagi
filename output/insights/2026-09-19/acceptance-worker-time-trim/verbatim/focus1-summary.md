# focus1 (修正後、計算ノード、-n 12、9 file 同走) と段 1 (修正前、file 単独走) の比較

| file | focus1 sum s | n | fail/error/skip | 段 1 sum s | n | 差 (段1−focus1) |
|---|---|---|---|---|---|---|
| test_run_tests_preflight | 72.9 | 217 | 0/0/0 | 206.7 | 216 | +133.7 |
| test_s8b_holdout_freeze | 402.7 | 164 | 0/0/2 | — | — | — |
| test_s8b_oracle_driver | 2972.6 | 158 | 0/0/6 | — | — | — |
| test_s8b_oracle_manifest | 3.1 | 97 | 0/0/0 | — | — | — |
| test_s8b_oracle_report | 43.8 | 269 | 0/0/0 | — | — | — |
| test_s8b_ratified_freeze | 134.9 | 91 | 1/0/0 | — | — | — |
| test_s8b_ratified_verify | 223.9 | 189 | 0/0/0 | 825.3 | 189 | +601.4 |
| test_s8b_verdict | 20.2 | 65 | 0/0/0 | — | — | — |
| test_t080_freeze_migration | 69.1 | 69 | 0/0/0 | — | — | — |

## 赤 (fail/error) の node
- test_s8b_ratified_freeze::test_emitter_memo_copy_matches_fresh_build (fail, 0.2s)

## 修正対象 file の上位 node (focus1)
### test_s8b_ratified_verify
-    8.96s (段1   15.09s) test_launch_validate_accepts_genuine_ineligible_earlier_resume
-    8.76s (段1   14.59s) test_g1_selection_helper_accepts_genuine_ineligible_earlier_resume
-    8.35s (段1   14.79s) test_launch_validate_rejects_genuine_eligible_earlier_official_run
-    8.34s (段1   14.61s) test_g1_selection_helper_rejects_genuine_eligible_earlier_official_run
-    7.46s (段1    7.32s) test_selector_parser_classification_boundary_at_ratified_launch
-    7.38s (段1   13.45s) test_generation_two_rejected_before_artifact_io
-    7.14s (段1   12.70s) test_chain_g2_env_tag_unchanged_loads
-    7.09s (段1    7.09s) test_selector_payload_is_not_exempt_and_conjunction_is_scanned
-    7.03s (段1    7.07s) test_selector_exact_exemption_accepts_declared_three_axis_evidence
-    6.81s (段1    6.36s) test_selector_launch_rejects_journal_row_decision_drift[static-decision-method]
-    6.80s (段1    6.48s) test_selector_exact_exemption_rejects_executable_h_mode
-    6.80s (段1    6.35s) test_selector_launch_rejects_journal_row_decision_drift[claim-decision-method]
### test_s8b_ratified_freeze
-   11.96s (段1 —) test_launch_rejects_invalid_v5_registry_proof[invalid:registry_schema]
-    8.43s (段1 —) test_launch_rejects_invalid_v5_registry_proof[missing:freeze_sha256]
-    7.21s (段1 —) test_degraded_launch_threads_expected_use_perf_to_every_consumer
-    6.24s (段1 —) test_launch_accepts_live_v5_registry_prefix_with_later_append
-    6.13s (段1 —) test_launch_rejects_invalid_v5_registry_proof[missing:registry_schema]
-    6.03s (段1 —) test_launch_rejects_invalid_v5_registry_proof[missing:schema]
-    5.95s (段1 —) test_launch_rejects_invalid_v5_registry_proof[missing:schedule_sha256]
-    5.78s (段1 —) test_launch_rejects_invalid_v5_registry_proof[invalid:row_count]
-    5.76s (段1 —) test_launch_rejects_invalid_live_v5_registry[shortened-attempt-registry-prefix-too-short]
-    5.76s (段1 —) test_launch_rejects_invalid_v5_registry_proof[invalid:schedule_sha256]
-    5.76s (段1 —) test_launch_rejects_invalid_v5_registry_proof[invalid:protocol_sha256]
-    5.75s (段1 —) test_launch_rejects_invalid_live_v5_registry[tampered-attempt-registry-replay-invalid]
### test_run_tests_preflight
-   14.64s (段1   11.89s) test_login_headroom_and_queue_four_quadrants[False-False-local]
-   14.57s (段1   11.89s) test_nonacceptance_bounded_child_marker_warns_exactly_once_in_parent
-   14.44s (段1   11.88s) test_login_headroom_and_queue_four_quadrants[True-False-local]
-   13.60s (段1   11.89s) test_login_headroom_and_queue_four_quadrants[True-True-local]
-   10.92s (段1   10.79s) test_previous_full_cap_estimate_dispatches_without_local_scope
-    1.13s (段1    1.09s) test_login_headroom_import_failure_falls_back_to_dispatch
-    1.11s (段1    1.05s) test_suspect_never_enters_local_admission
-    1.10s (段1    1.04s) test_suspect_execution_refuses_without_dispatch_or_xdist
-    0.10s (段1 —) test_small_login_repo_fixture_yields_real_fingerprint
-    0.07s (段1   11.89s) test_login_non_immediate_dispatch_exempt_flags_enter_bounded_scope[--collect-only]
-    0.07s (段1   11.90s) test_without_force_dispatch_login_with_headroom_still_runs_local
-    0.07s (段1    8.26s) test_login_local_scope_releases_budget_lease_on_interrupt

## 赤の本文 (親が log から抜粋)
- `test_s8b_ratified_freeze.py::test_emitter_memo_copy_matches_fresh_build` は `orchestrator/campaign/s8b_expected_materialization.py:1421` の
  `ExpectedMaterializationError: snapshot fork requires exactly one OS thread` で失敗した (最初の fresh 構築 `/tmp/izanagi-emitter-fresh-*/repo/external/ccbench` の sealed build session)。
  builder は sealed build session で fork するため、呼び出し process が単一 OS thread でなければならない。xdist worker は多 thread なので、
  既存の builder 利用 test は `@in_sealed_fixture_process` (fork 子 = 単一 thread) で本体を走らせている。新 test は親 (裁定 §2 項 8) の指示で decorator を付けなかった → 親の指示ミス。
  fix 方針: 新 test に `@in_sealed_fixture_process` を付ける (disk memo は fork 子でも残るので test の検証内容は変わらない)。
- 他 1310 node は緑 (F 90 node、V 189 node、R 216 node + 新 1、consumer 5 file)。

## 実測条件の注記
- focus1 は 9 file 同走 (`-n 12`) で、段 1 は file 単独走 (`-n 12`)。条件が違うので、差 (V −601 s、R −134 s) は異条件の観測差であり、因果的な削減秒や下限としては扱わない。削減秒は同 job・同条件の A/B で出す (レビュー B 所見 2 で訂正)。
- V で ~7 s のまま変わらない node は `selector_valid_cell=True` / `selector_payload_hit=True` で memo を迂回する test (設計どおり)。
- R で 11〜15 s のまま残る node = 除外した `test_login_headroom_and_queue_four_quadrants[*-local]` 3 本、`test_nonacceptance_bounded_child_marker_warns_exactly_once_in_parent`、`test_previous_full_cap_estimate_dispatches_without_local_scope`。
- junit の file 別 (秒): V 825.3→223.9、R 206.7→72.9、F 134.9 (段 1 未計測)。
