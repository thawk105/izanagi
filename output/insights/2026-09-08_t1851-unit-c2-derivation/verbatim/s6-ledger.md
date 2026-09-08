## 実行した argv

```text
python3 tools/update_acceptance_duration_ledger.py --help
python3 tools/update_acceptance_duration_ledger.py --add-only /work/1/SFC/tanab/.izanagi-acceptance-shards/e04319292c80256eba45349c4a6a061c/junit.xml
PYTHONPATH=. python3 orchestrator/tests/test_acceptance_schedule_order.py
```

`--repo` と `--output` の既定値が指定された作業 root と台帳を指すことを確認しました。

## 生成器の報告 (added / skipped / excluded)

```text
added=2142
skipped_existing=20176
excluded_failure_or_error=1
excluded_frozen_removed=0
excluded_writer_base_key=1
excluded_frozen_suite=139
excluded_total=141
```

## 登録前後の nodeid_count と実体数

```text
登録前: nodeid_count=20284 / 実体数=20284
登録後: nodeid_count=22426 / 実体数=22426
```

`schema_version=1`、`unit="seconds"` も維持されています。

## 削除 0 件・既存値変更 0 件の検算

```text
削除された nodeid: 0
既存 duration 値の変更: 0
既存 entry の byte 変更: 0
追加された nodeid: 2142
```

登録前スナップショットとの全件比較で検算しました。

## 追加された nodeid の内訳 (file 別の件数)

97 files、合計 2,142 件です。

```text
orchestrator/tests/test_a5_second_boot_job_contract.py: 7
orchestrator/tests/test_artifact_admission.py: 13
orchestrator/tests/test_autonomous_trial_completeness.py: 1
orchestrator/tests/test_axis1_search_runner.py: 23
orchestrator/tests/test_axis_b5_search_catalog.py: 17
orchestrator/tests/test_b10_backoff_shape_sweep.py: 117
orchestrator/tests/test_b10_extended_figure_provenance.py: 3
orchestrator/tests/test_backoff_consumers.py: 4
orchestrator/tests/test_backoff_counterfactual_analysis.py: 25
orchestrator/tests/test_backoff_extended_sweep.py: 11
orchestrator/tests/test_backoff_overthrottle.py: 1
orchestrator/tests/test_backoff_sweep.py: 2
orchestrator/tests/test_bench_first_real_wal.py: 1
orchestrator/tests/test_between_run_floor.py: 2
orchestrator/tests/test_buildcache_v2.py: 8
orchestrator/tests/test_calibrator.py: 1
orchestrator/tests/test_calibrator_certify.py: 13
orchestrator/tests/test_calibrator_deferred_output.py: 1
orchestrator/tests/test_campaign.py: 11
orchestrator/tests/test_campaign_lock_codec.py: 47
orchestrator/tests/test_ccbench_spawn_sites.py: 26
orchestrator/tests/test_check_docs.py: 1
orchestrator/tests/test_codex_agents.py: 5
orchestrator/tests/test_codex_reasoning_ab.py: 8
orchestrator/tests/test_condition_meaning_gate.py: 63
orchestrator/tests/test_dev_wave_land.py: 12
orchestrator/tests/test_dynamic_backoff_transitions.py: 69
orchestrator/tests/test_external_acceptance_signing.py: 22
orchestrator/tests/test_flaky_test_holds_contract.py: 1
orchestrator/tests/test_floor_pair_driver.py: 211
orchestrator/tests/test_hooks.py: 17
orchestrator/tests/test_knowledge_manifest.py: 46
orchestrator/tests/test_layer3_report.py: 37
orchestrator/tests/test_masstree_archive_projection.py: 8
orchestrator/tests/test_mocc_proof_surface.py: 18
orchestrator/tests/test_mocc_trace_job_contract.py: 42
orchestrator/tests/test_mutation_fanout_contract.py: 8
orchestrator/tests/test_mutation_harness.py: 12
orchestrator/tests/test_p3_autonomous_workload_trial.py: 19
orchestrator/tests/test_p3_b4_analysis_ledgers.py: 4
orchestrator/tests/test_p3_b4_floor_artifact_issuer.py: 6
orchestrator/tests/test_p3_b4_material_report.py: 7
orchestrator/tests/test_p3_b4_prerun_issuer.py: 5
orchestrator/tests/test_p3_b4_producer_auth_experiment.py: 50
orchestrator/tests/test_p3_b4_raw_record_producer.py: 21
orchestrator/tests/test_p3_s4_loop.py: 79
orchestrator/tests/test_p3_s4_loop_job_contract.py: 71
orchestrator/tests/test_p3_s4_loop_trigger_gating.py: 2
orchestrator/tests/test_paper_story_a1_paired.py: 17
orchestrator/tests/test_paper_story_a2_certification.py: 78
orchestrator/tests/test_paper_story_a2_job_contract.py: 23
orchestrator/tests/test_pegasus_calibration_workload.py: 3
orchestrator/tests/test_pegasus_dispatch_compute.py: 16
orchestrator/tests/test_pegasus_floor_tools.py: 14
orchestrator/tests/test_pegasus_tools.py: 4
orchestrator/tests/test_plot_a2_certification.py: 79
orchestrator/tests/test_plot_b10_extended_backoff.py: 3
orchestrator/tests/test_plot_backoff_ci.py: 2
orchestrator/tests/test_plot_dynamic_backoff.py: 19
orchestrator/tests/test_plot_t2187_adaptive_consts.py: 7
orchestrator/tests/test_plot_t2266_tail_mechanism.py: 22
orchestrator/tests/test_reflux_formal_consumer.py: 30
orchestrator/tests/test_reflux_result_evidence.py: 44
orchestrator/tests/test_related_work_search.py: 108
orchestrator/tests/test_s1_known_axes_freeze.py: 4
orchestrator/tests/test_s1_report.py: 1
orchestrator/tests/test_s8b_floor_campaign.py: 35
orchestrator/tests/test_s8b_floor_contract.py: 1
orchestrator/tests/test_s8b_floor_stats.py: 25
orchestrator/tests/test_s8b_holdout_admission.py: 44
orchestrator/tests/test_s8b_holdout_freeze.py: 1
orchestrator/tests/test_s8b_oracle_judge.py: 3
orchestrator/tests/test_s8b_oracle_manifest.py: 5
orchestrator/tests/test_s8b_oracle_report.py: 2
orchestrator/tests/test_s8b_ratified_freeze.py: 3
orchestrator/tests/test_s8b_ratified_verify.py: 4
orchestrator/tests/test_s8b_terminal_evidence.py: 4
orchestrator/tests/test_s8b_verdict.py: 2
orchestrator/tests/test_s8c_acceptance_receipt_v2.py: 14
orchestrator/tests/test_s8c_budget.py: 10
orchestrator/tests/test_s8c_cli_entrypoints.py: 16
orchestrator/tests/test_s8c_preregistration_core.py: 32
orchestrator/tests/test_s8c_preregistration_predicates.py: 3
orchestrator/tests/test_schema_v2.py: 6
orchestrator/tests/test_screening_driver.py: 8
orchestrator/tests/test_sort_swo_dependency_material.py: 3
orchestrator/tests/test_t126_pegasus_tools.py: 3
orchestrator/tests/test_t1286_commit_receipt.py: 2
orchestrator/tests/test_t1434_t1222_science_slice.py: 4
orchestrator/tests/test_t189_oracle_wiring_slice.py: 3
orchestrator/tests/test_t2187_adaptive_const_probe.py: 118
orchestrator/tests/test_t2216_backoff_walk_model.py: 53
orchestrator/tests/test_t2228_driver_gate_liveness_probe.py: 14
orchestrator/tests/test_t2337_dispatch_timeout_overrides.py: 21
orchestrator/tests/test_t671_source_binding.py: 4
orchestrator/tests/test_trial_registry.py: 23
orchestrator/tests/test_verifier.py: 24
```

## 実走した nodeid と結果

```text
orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection
PASS
```

ファイル全体の実走結果:

```text
79 passed, 1 warning in 148.56s
exit code: 0
effective_scheduler: serial
```

## 総括

[acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-ledger2/orchestrator/tests/acceptance_duration_ledger.json) に生成器の `--add-only` で 2,142 nodeid を追加し、被覆率検査は緑になりました。Git・commit・手編集は行わず、検算用一時ファイルも削除済みです。