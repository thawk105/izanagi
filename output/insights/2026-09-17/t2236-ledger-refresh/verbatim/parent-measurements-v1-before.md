# 親の実測 1: shard 別 (実測 wall / 直列和 / 台帳予測 / 未登録) — session d3ebafc0 と 6571431e、現行台帳 (main b4631a92e、sha256 81ecfdf0…)

script: /home/SFC/tanab/.claude/jobs/897c9a22/tmp/analyze_shards.py

== d3ebafc08d3d12c86081dcd356ebb80c
  shard-0: n=8824 wall=350.994 serial_actual=8852.3 ledger_pred=5701.2 unknown=459 unknown_actual=678.3
     heavy unknown (159.2, 'orchestrator/tests/test_s1_known_axes_freeze.py::test_historical_oracle_nonadapter_reaches_current_semantics')
     heavy unknown (153.1, 'orchestrator/tests/test_s8b_oracle_driver.py::test_t080_shared_base_builds_real_builder_once_across_processes')
     heavy unknown (67.0, 'orchestrator/tests/test_sort_swo_oracle.py::test_trusted_evaluator_matches_real_tu_for_all_79_ir_values')
     heavy unknown (66.6, 'orchestrator/tests/test_real_repo_serialization.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes')
     heavy unknown (33.7, 'orchestrator/tests/test_real_repo_serialization.py::test_t080_output_snapshot_detects_git_visible_real_output_changes')
     heavy unknown (33.5, 'orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_accept_static[replay]')
     heavy unknown (33.3, 'orchestrator/tests/test_real_repo_serialization.py::test_t080_output_snapshot_observes_git_visible_create_and_delete')
     heavy unknown (31.5, 'orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_reject_swap_restore[replay]')
  shard-1: n=8128 wall=238.476 serial_actual=4432.9 ledger_pred=5700.4 unknown=314 unknown_actual=229.7
     heavy unknown (37.1, 'orchestrator/tests/test_s8b_holdout_freeze.py::test_restored_namespace_restores_candidate_inputs')
     heavy unknown (35.8, 'orchestrator/tests/test_s8b_holdout_freeze.py::test_restored_namespace_rejects_later_eligible_run')
     heavy unknown (4.4, 'orchestrator/tests/test_s8b_expected_materialization.py::test_sealed_session_disconnect_stop_and_supervisor_death_are_contained')
     heavy unknown (3.9, 'orchestrator/tests/test_critic.py::test_current_v4_and_legacy_v3_v2_loaders_are_generation_exact')
     heavy unknown (3.6, 'orchestrator/tests/test_s8b_expected_materialization.py::test_sealed_capability_exact_identity_and_binary_manifest_bindings')
     heavy unknown (3.6, 'orchestrator/tests/test_p3_autonomous_workload_trial.py::test_origin_runtime_collects_only_producer_owned_evidence[symlink-record]')
     heavy unknown (3.5, 'orchestrator/tests/test_s8b_expected_materialization.py::test_normal_unmount_busy_control_and_session_issue_rejection')
     heavy unknown (3.4, 'orchestrator/tests/test_p3_autonomous_workload_trial.py::test_origin_runtime_collects_only_producer_owned_evidence[symlink-parent]')
  shard-2: n=7616 wall=202.659 serial_actual=4518.6 ledger_pred=5700.4 unknown=794 unknown_actual=210.5
     heavy unknown (18.7, 'orchestrator/tests/test_t316_sandbox_probe.py::test_s6_live_requested_gate_and_both_build_roots_match')
     heavy unknown (18.7, 'orchestrator/tests/test_t316_sandbox_probe.py::test_s6_live_requested_checkout_reaches_terminal_without_host_tmpdir[unset]')
     heavy unknown (17.3, 'orchestrator/tests/test_t316_sandbox_probe.py::test_s6_live_requested_checkout_reaches_terminal_without_host_tmpdir[/tmp]')
     heavy unknown (14.4, 'orchestrator/tests/test_check_ai_provenance.py::test_receipt_retention_prunes_oldest')
     heavy unknown (12.2, 'orchestrator/tests/test_t316_sandbox_probe.py::test_s6_live_patch_cleanup_on_short_circuit_and_gate_exception[outside]')
     heavy unknown (10.4, 'orchestrator/tests/test_t316_sandbox_probe.py::test_s6_live_patch_cleanup_on_short_circuit_and_gate_exception[gate]')
     heavy unknown (8.7, 'orchestrator/tests/test_t126_pegasus_tools.py::test_archived_submission_uses_checkout_dependency_staging[missing-gflags]')
     heavy unknown (8.5, 'orchestrator/tests/test_t316_sandbox_probe.py::test_s6_requested_checkout_avoids_masked_tmp[/tmp]')
== 6571431ebd0ffae08a4830ef4c33e502
  shard-0: n=9324 wall=344.319 serial_actual=8857.6 ledger_pred=5687.2 unknown=435 unknown_actual=702.4
     heavy unknown (154.7, 'orchestrator/tests/test_s1_known_axes_freeze.py::test_historical_oracle_nonadapter_reaches_current_semantics')
     heavy unknown (153.4, 'orchestrator/tests/test_s8b_oracle_driver.py::test_t080_shared_base_builds_real_builder_once_across_processes')
     heavy unknown (69.8, 'orchestrator/tests/test_sort_swo_oracle.py::test_trusted_evaluator_matches_real_tu_for_all_79_ir_values')
     heavy unknown (69.6, 'orchestrator/tests/test_real_repo_serialization.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes')
     heavy unknown (41.2, 'orchestrator/tests/test_real_repo_serialization.py::test_t080_output_snapshot_observes_git_visible_create_and_delete')
     heavy unknown (41.1, 'orchestrator/tests/test_real_repo_serialization.py::test_t080_output_snapshot_detects_git_visible_real_output_changes')
     heavy unknown (22.4, 'orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_accept_static[replay]')
     heavy unknown (20.2, 'orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_reject_swap_restore[replay]')
  shard-1: n=7775 wall=236.282 serial_actual=4388.1 ledger_pred=5686.4 unknown=349 unknown_actual=187.9
     heavy unknown (35.4, 'orchestrator/tests/test_s8b_holdout_freeze.py::test_restored_namespace_restores_candidate_inputs')
     heavy unknown (32.0, 'orchestrator/tests/test_s8b_holdout_freeze.py::test_restored_namespace_rejects_later_eligible_run')
     heavy unknown (9.1, 'orchestrator/tests/test_t316_sandbox_probe.py::test_s6_live_requested_checkout_reaches_terminal_without_host_tmpdir[unset]')
     heavy unknown (8.3, 'orchestrator/tests/test_t316_sandbox_probe.py::test_s6_live_requested_gate_and_both_build_roots_match')
     heavy unknown (8.1, 'orchestrator/tests/test_t316_sandbox_probe.py::test_s6_live_requested_checkout_reaches_terminal_without_host_tmpdir[/tmp]')
     heavy unknown (6.3, 'orchestrator/tests/test_t316_sandbox_probe.py::test_s6_live_patch_cleanup_on_short_circuit_and_gate_exception[outside]')
     heavy unknown (5.2, 'orchestrator/tests/test_critic.py::test_current_v4_and_legacy_v3_v2_loaders_are_generation_exact')
     heavy unknown (3.5, 'orchestrator/tests/test_t316_sandbox_probe.py::test_s6_live_patch_cleanup_on_short_circuit_and_gate_exception[gate]')
  shard-2: n=7427 wall=201.474 serial_actual=4299.3 ledger_pred=5686.4 unknown=741 unknown_actual=115.5
     heavy unknown (14.9, 'orchestrator/tests/test_check_ai_provenance.py::test_receipt_retention_prunes_oldest')
     heavy unknown (11.9, 'orchestrator/tests/test_t126_pegasus_tools.py::test_archived_submission_uses_checkout_dependency_staging[hydrated]')
     heavy unknown (11.8, 'orchestrator/tests/test_t126_pegasus_tools.py::test_archived_submission_uses_checkout_dependency_staging[missing-gflags]')

# 親の実測 2: file 別の台帳値と実測の差 (session d3ebafc0、|delta| > 30 秒のみ、FROZEN = _ADD_ONLY_FROZEN_SUITE_PREFIXES)

script: /home/SFC/tanab/.claude/jobs/897c9a22/tmp/analyze_files.py

file shard actual_known pred_known delta n_known n_unknown actual_unknown frozen
orchestrator/tests/test_s8b_oracle_driver.py s0 2661 676 +2126 134 13 153
orchestrator/tests/test_s8b_floor_campaign.py s0 2366 1073 +1289 516 12 9
orchestrator/tests/test_s8b_ratified_verify.py s2 945 246 +699 189 0 0
orchestrator/tests/test_run_tests_preflight.py s2 545 223 +323 216 0 0
orchestrator/tests/test_t139_submission_path.py s0 344 93 +252 25 0 0
orchestrator/tests/test_codex_reasoning_ab.py s0 394 244 +230 636 7 87
orchestrator/tests/test_p3_b4_producer_auth_experiment.py s1 830 611 +219 50 0 0
orchestrator/tests/test_s8c_preregistration_predicates.py s0 329 136 +193 218 0 0
orchestrator/tests/test_t338_submission_gate_unit5.py s1 275 92 +183 58 0 0
orchestrator/tests/test_s8b_ratified_freeze.py s1 405 245 +160 82 0 0
orchestrator/tests/test_s1_known_axes_freeze.py s0 1 0 +154 46 13 167
orchestrator/tests/test_s8b_holdout_freeze.py s1 418 352 +136 159 5 74
orchestrator/tests/test_sort_swo_oracle.py s0 110 41 +114 66 38 83 FROZEN
orchestrator/tests/test_real_repo_serialization.py s0 133 117 +103 42 53 140 FROZEN
orchestrator/tests/test_t316_sandbox_probe.py s2 4 3 +86 129 37 122
orchestrator/tests/test_s8b_verdict.py s2 118 34 +84 65 0 0
orchestrator/tests/test_t1998_stock_inline_pair.py s0 74 3 +70 38 1 0
orchestrator/tests/test_ccbench_spawn_sites.py s2 224 155 +69 47 0 0
orchestrator/tests/test_spool_fold.py s0 110 65 +46 167 0 0
orchestrator/tests/test_check_docs.py s1 246 202 +42 575 2 0
orchestrator/tests/test_s8b_oracle_judge.py s1 75 34 +40 55 0 0
orchestrator/tests/test_check_ai_provenance.py s2 227 146 +38 366 96 53
orchestrator/tests/test_s8c_gate_report.py s0 78 41 +36 21 0 0
orchestrator/tests/test_dev_wave_land.py s1 174 136 +33 312 9 4
orchestrator/tests/test_flaky_test_holds_contract.py s2 19 52 -34 38 0 0
orchestrator/tests/test_p3_exploration_namespace.py s1 5 24 -35 15 20 5 FROZEN
orchestrator/tests/test_acceptance_schedule_order.py s0 56 91 -36 79 0 0
orchestrator/tests/test_t126_qualification_driver.py s2 2 30 -36 33 8 0
orchestrator/tests/test_layer3_admission_diagnosis.py s0 1 39 -37 23 0 0
orchestrator/tests/test_check_branch_landed.py s0 7 7 -39 54 42 2
orchestrator/tests/test_s8c_preregistration_invariant.py s0 45 97 -52 20 0 0
orchestrator/tests/test_p3_s4_loop_trigger_gating.py s0 33 86 -53 124 0 0
orchestrator/tests/test_related_work_search.py s1 170 229 -59 121 0 0
orchestrator/tests/test_insights_date_layout.py s2 0 0 -60 0 62 2
orchestrator/tests/test_verify_fanout.py s1 2 64 -62 41 0 0
orchestrator/tests/test_p3_autonomous_workload_trial.py s1 84 151 -67 266 24 24
orchestrator/tests/test_p3_b4_floor_artifact_issuer.py s2 0 0 -69 24 70 1
orchestrator/tests/test_t126_qualification_artifacts.py s0 2 73 -71 59 0 0
orchestrator/tests/test_p3_s4_loop_sort.py s0 22 70 -75 29 29 3 FROZEN
orchestrator/tests/test_b10_backoff_grid_job.py s2 0 0 -76 0 78 2
orchestrator/tests/test_b10_backoff_grid_submit.py s0 0 0 -92 0 98 6
orchestrator/tests/test_s1_direct_comparison.py s0 31 90 -94 97 42 7 FROZEN
orchestrator/tests/test_t126_pegasus_tools.py s2 383 498 -104 276 6 17
orchestrator/tests/test_t2187_adaptive_const_probe.py s2 206 212 -115 186 109 0
orchestrator/tests/test_artifact_admission.py s2 29 93 -152 146 93 5
orchestrator/tests/test_p3_s4_loop.py s0 114 270 -158 411 3 0
orchestrator/tests/test_p3_b4_raw_record_producer.py s2 382 546 -164 50 0 0
orchestrator/tests/test_p3_b4_closed_critic.py s2 141 312 -172 72 0 0
orchestrator/tests/test_s8b_oracle_report.py s1 142 316 -174 269 0 0
orchestrator/tests/test_campaign.py s0 152 353 -203 416 2 0
orchestrator/tests/test_layer3_report.py s1 20 244 -242 216 21 2
orchestrator/tests/test_critic.py s1 16 347 -346 117 23 8 FROZEN
orchestrator/tests/test_trial_registry.py s1 305 713 -451 248 47 4
orchestrator/tests/test_t1259_qsub_env_delivery_probe.py s0 546 1025 -479 51 0 0
orchestrator/tests/test_paper_story_a1_paired.py s2 52 664 -701 196 91 1
orchestrator/tests/test_autonomous_trial_completeness.py s1 74 778 -703 283 0 0
orchestrator/tests/test_p3_b4_wiring_probe.py s2 110 906 -796 65 0 0
total delta 702 frozen-suite delta -334
