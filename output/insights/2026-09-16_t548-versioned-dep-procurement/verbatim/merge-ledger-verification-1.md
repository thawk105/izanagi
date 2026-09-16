## 総括

**編集 0 件・検証のみ。全 pin が merge 後の現物と一致しました。**

- 自走 harness：**47 passed、rc=0、234.49 秒**
- 本数・行番号以外の問題：なし
- `git diff --exit-code`：rc=0。既存 index に対する追加差分なし
- HEAD：`e667c8c13`。index・HEAD を変更する操作は実施していません。

実行コマンド：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 orchestrator/tests/test_ccbench_spawn_sites.py
```

実走範囲は同 file の全 47 nodeid（46 test 関数、parameter 展開込み）。次の対象 nodeid もすべて成功しています。

- `orchestrator/tests/test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_has_no_unreviewed_ungated_member`
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_t2520_certify_entry_removal`

照合は source 全文の AST から scope・呼び出し位置・本数を取得して行いました。合成 source についても、テスト内の文字列を AST 解析して確認しています。

**実 source の行番号 pin 一覧**

以下の scope はすべて先頭の `<module>.` を省略しています。最初の 8 entry は `_DEFERRED_GATE_MEMBERS` と exact 集合の両方を確認済みです。3941 は別テストの記載も含め、計 3 箇所を確認しました。

| Source file:line | Entry | pin | 結果 |
|---|---|---:|---|
| `orchestrator/campaign/b4_binary_record.py:118` | `_build_with_dependencies` | 118 | 一致 |
| `orchestrator/campaign/b10_backoff_shape_sweep.py:3644` | `_build_binary` | 3644 | 一致 |
| `orchestrator/campaign/b10_backoff_shape_sweep.py:4470` | `run_formal` | 4470 | 一致 |
| `orchestrator/campaign/paper_story_a1_paired.py:7423` | `run_measurement` | 7423 | 一致 |
| `orchestrator/campaign/s8b_floor_campaign.py:4722` | `build_cells.invoke_build` | 4722 | 一致 |
| `orchestrator/campaign/s8b_floor_campaign.py:8675` | `main` | 8675 | 一致 |
| `tools/pegasus/probes/t2187_adaptive_const_probe.py:3941` | `_certify_main._build_trace_binary` | 3941 | 一致 |
| `tools/pegasus/probes/t2187_adaptive_const_probe.py:4334` | `main` | 4334 | 一致 |
| `orchestrator/campaign/s1_direct_comparison.py:1281` | `run_role` | 1281 | 一致 |
| `orchestrator/campaign/s8b_oracle_driver.py:1783` | `run_block` | 1783 | 一致 |

**起動本数 pin 全一覧**

143 pin、141 scope、160 起動箇所を確認し、未登録 scope もありませんでした。

表の file は `orchestrator/` 相対です。各項目の表記は **`scope = 本数 pin @ source 行番号`**。scope の `<module>.` は省略しています。`1+1` は別分類にある 2 pin です。

| Source file | Entry・pin・現物の行番号 | 結果 |
|---|---|---|
| `calibrator/cli.py` | `_assert_trace_disabled_binary = 1 @ 205` | 一致 |
| `calibrator/perf_preflight.py` | `probe_perf_availability = 1 @ 122` | 一致 |
| `calibrator/runner.py` | `competing_bench_pids = 1 @ 405`<br>`composite_competing_probe = 2 @ 459,477`<br>`run_once = 1 @ 663` | 全件一致 |
| `calibrator/tsc.py` | `_build_helper = 1 @ 73`<br>`measure_tsc = 1 @ 95` | 全件一致 |
| `campaign/artifact_admission.py` | `_git_snapshot_sha256 = 1 @ 677` | 一致 |
| `campaign/b10_backoff_shape_sweep.py` | `_git = 1 @ 615`<br>`_measure_probe_binary = 1 @ 2446`<br>`_run_probe_command = 1 @ 2332`<br>`load_preregistration = 1 @ 1782` | 全件一致 |
| `campaign/b10_backoff_static_tail_formal.py` | `_git = 1 @ 227`<br>`scheduler_coordinates = 1 @ 726` | 全件一致 |
| `campaign/b4_binary_record.py` | `_install_dependency = 1 @ 57`<br>`prepare_dependencies = 1 @ 79` | 全件一致 |
| `campaign/backoff_extended_sweep.py` | `_git_worktree_output = 1 @ 143` | 一致 |
| `campaign/backoff_profile.py` | `_profile_run = 1+1 @ 757,769` | 一致 |
| `campaign/backoff_requested_us.py` | `_run_rep = 1 @ 904` | 一致 |
| `campaign/buildcache.py` | `_assert_no_trace_symbols = 1 @ 3773`<br>`_observe_fetchcontent_dependency_receipt = 1 @ 959`<br>`_run = 1 @ 3805`<br>`_tool_version = 1 @ 1194`<br>`_tool_version_full = 1 @ 1228`<br>`_verify_ccbench_commit = 1 @ 3831` | 全件一致 |
| `campaign/certified_writer_admission.py` | `_git = 1 @ 108` | 一致 |
| `campaign/certified_writer_preflight.py` | `_committed_blob = 1 @ 68` | 一致 |
| `campaign/condition_meaning_gate.py` | `_run_process = 1 @ 1597` | 一致 |
| `campaign/contract_loader_binding.py` | `_run_git = 1 @ 293` | 一致 |
| `campaign/floor_job_checkpoint.py` | `_bounded_boolean_child = 1 @ 150` | 一致 |
| `campaign/floor_liveness.py` | `classify = 1 @ 730` | 一致 |
| `campaign/floor_pair_driver.py` | `_git_head = 1 @ 560`<br>`_git_is_ancestor = 1 @ 585`<br>`_git_show_head = 1 @ 540`<br>`_run_probe = 1 @ 1623` | 全件一致 |
| `campaign/knowledge_manifest.py` | `_git = 1 @ 411` | 一致 |
| `campaign/layer3_report.py` | `_git_head = 1 @ 181` | 一致 |
| `campaign/mocc_trace_pair_anchor.py` | `_verify_ed25519_signature = 1 @ 313` | 一致 |
| `campaign/p3_b4_admission_record.py` | `_git_call = 1 @ 315` | 一致 |
| `campaign/p3_b4_producer_auth_experiment.py` | `ScratchTree.__enter__ = 5 @ 1893,1900,1914,1927,1942`<br>`producer_blob_at_commit = 1 @ 665`<br>`repository_status_bytes = 1 @ 1853`<br>`resolve_source_head = 1 @ 639` | 全件一致 |
| `campaign/paper_story_a1_paired.py` | `_observe_qstat_visibility = 1 @ 3034`<br>`_observe_scheduler_terminal = 1 @ 3936`<br>`_run_git = 1 @ 2368`<br>`_run_qsub = 1 @ 2999` | 全件一致 |
| `campaign/paper_story_a2_certification.py` | `compute_preflight = 2 @ 4937,4943`<br>`exact_qsub = 1 @ 2213`<br>`finish_group = 1 @ 2237`<br>`run_workload = 3 @ 3697,3702,3707` | 全件一致 |
| `campaign/patchharness.py` | `_git = 1 @ 90`<br>`_git_repository_identity = 1 @ 288` | 全件一致 |
| `campaign/pipeline.py` | `_current_repo_head = 1 @ 742`<br>`_default_verify_fanout_launcher = 1 @ 839`<br>`_require_canonical_build_source_state._git = 1 @ 1109`<br>`_run_trace = 1 @ 446` | 全件一致 |
| `campaign/queue_state.py` | `_run_qstat_bounded = 1 @ 151` | 一致 |
| `campaign/reflux_origin_ledger.py` | `_git = 1 @ 1707` | 一致 |
| `campaign/reflux_source_closure.py` | `_git = 1 @ 133` | 一致 |
| `campaign/s1_known_axes_freeze.py` | `_run_git = 1 @ 199` | 一致 |
| `campaign/s1_measurement_freeze.py` | `_run_git = 1 @ 106` | 一致 |
| `campaign/s1_report.py` | `_git_head = 1 @ 909` | 一致 |
| `campaign/s1_verify_extime_calibration.py` | `_run_once = 1 @ 290`<br>`_verifier_run = 1 @ 325` | 全件一致 |
| `campaign/s2_verify_calibration.py` | `_broken_build_and_verify = 1 @ 321`<br>`_run_cmake_build = 1 @ 287`<br>`_run_once = 1 @ 160`<br>`_verifier_run = 1 @ 204` | 全件一致 |
| `campaign/s3_lock_coverage.py` | `_build_broken = 1 @ 220`<br>`_run_cmake_build = 1 @ 192`<br>`_run_trace = 1 @ 139`<br>`_verify = 1 @ 169` | 全件一致 |
| `campaign/s3_mocc_lock_coverage.py` | `_run_checked = 1 @ 106`<br>`_run_trace = 1 @ 351` | 全件一致 |
| `campaign/s5_permutation_coverage.py` | `_build_broken = 1 @ 253`<br>`_run_cmake_build = 1 @ 225`<br>`_run_trace = 1 @ 136`<br>`_verify = 1 @ 199` | 全件一致 |
| `campaign/s6_canary_rename.py` | `export_stock = 3 @ 192,196,200`<br>`git_apply = 1 @ 205`<br>`normalize_cxx = 1 @ 217`<br>`verify = 1 @ 267` | 全件一致 |
| `campaign/s6_proposal_rounds.py` | `call_headless = 1 @ 333`<br>`cmd_freeze = 1 @ 211`<br>`freshness_check = 2 @ 99,113` | 全件一致 |
| `campaign/s8a_trigger_coverage.py` | `_build = 1 @ 249`<br>`_run_cmake_build = 1 @ 175`<br>`_run_trace = 1 @ 264`<br>`_verify = 1 @ 297` | 全件一致 |
| `campaign/s8a_trigger_freq.py` | `_run_freq = 1+1 @ 95,106` | 一致 |
| `campaign/s8b_expected_materialization.py` | `SealedBuildSession._start = 1 @ 1422`<br>`_snapshot_guardian = 1 @ 1315`<br>`_snapshot_supervisor = 1 @ 1258`<br>`_snapshot_worker = 1 @ 1218` | 全件一致 |
| `campaign/s8b_floor_attempt_launcher.py` | `_owned_post_probe = 1 @ 619` | 一致 |
| `campaign/s8b_floor_campaign.py` | `_ccbench_gitlink = 1 @ 1081`<br>`_default_probe_fn = 1 @ 1688`<br>`_floor_protocol_paths_at_commit = 1 @ 884`<br>`_head_blob_100644 = 2 @ 787,807`<br>`_head_commit_oid = 1 @ 767`<br>`_observe_floor_tool = 1 @ 4108`<br>`_pre_oracle_blob = 2 @ 5190,5205`<br>`_verify_floor_oracle_dependency_source = 1 @ 2877`<br>`_verify_pristine_floor_dependency_sources = 2 @ 2672,2748` | 全件一致 |
| `campaign/s8b_holdout_admission.py` | `_run_git = 1 @ 603` | 一致 |
| `campaign/s8b_holdout_freeze.py` | `_run_git = 1 @ 295`<br>`_run_git_bytes = 1 @ 309`<br>`_run_git_z = 1 @ 336` | 全件一致 |
| `campaign/s8b_oracle_n_pilot.py` | `_git_output = 1 @ 575`<br>`_observe_toolchain = 1 @ 800` | 全件一致 |
| `campaign/s8b_prediction_runner.py` | `_git_bytes = 1 @ 1304` | 一致 |
| `campaign/s8b_ratified_freeze.py` | `_git = 1 @ 313`<br>`_git_ok = 1 @ 331` | 全件一致 |
| `campaign/s8b_selector_freeze.py` | `_verify_commit_pin = 1 @ 149` | 一致 |
| `campaign/s8c_acceptance_receipt.py` | `_git = 1 @ 1049` | 一致 |
| `campaign/s8c_preregistration.py` | `_git = 1 @ 1094` | 一致 |
| `campaign/silo_ladder_rung1.py` | `_pinned_patched_source_model = 2 @ 1917,1961`<br>`_run = 2 @ 367,380` | 全件一致 |
| `campaign/sort_swo_dependency_material.py` | `_run_git = 1 @ 105` | 一致 |
| `campaign/sort_swo_oracle.py` | `_broker_main = 1 @ 2003`<br>`_compile = 1 @ 2551`<br>`_compiler_version = 1 @ 3138`<br>`_dependency_manifest_closure = 1 @ 2492`<br>`_run_matrix = 1 @ 2673` | 全件一致 |
| `campaign/source_digest.py` | `_checkout_gitlink_oid = 2 @ 1471,1486`<br>`_cpp_normalize = 1 @ 1668`<br>`_dump_macros = 1 @ 1712`<br>`_git_show = 1 @ 1946`<br>`_git_tree_entries = 1 @ 1397`<br>`_tracked_diff_sha256 = 1 @ 2351`<br>`_tracked_status_paths = 1 @ 2312` | 全件一致 |
| `campaign/t080_freeze_migration.py` | `_git = 1 @ 579`<br>`_git_rc = 1 @ 623` | 全件一致 |
| `campaign/t152_write_intent_coverage.py` | `_run_process = 1 @ 154`<br>`_verify = 1 @ 533` | 全件一致 |
| `campaign/t1998_stock_inline_pair.py` | `_preregistration_blob = 1 @ 373`<br>`load_preregistration = 1 @ 402` | 全件一致 |
| `campaign/t810_validator.py` | `_git = 1 @ 350` | 一致 |
| `campaign/trial_registry.py` | `_git = 1 @ 975` | 一致 |
| `campaign/verify_fanout_worker.py` | `_repo_head = 1 @ 409` | 一致 |

二重分類は現物の内容も確認しました。`backoff_profile.py` は 757 が測定、769 が report、`s8a_trigger_freq.py` は 95 が診断実行、106 が awk 集計です。

**関連する呼び出し・import 本数 pin**

| Source file:line | Entry | pin | 結果 |
|---|---|---:|---|
| `orchestrator/campaign/b10_backoff_shape_sweep.py:2685` | `measure_performance_cell` の `run_once` | 1 | 一致 |
| `orchestrator/campaign/backoff_overthrottle.py:363` | `_run_rep` の `run_once` | 1 | 一致 |
| `orchestrator/calibrator/cli.py:986` | `_certify_main` の capability issuer 呼び出し | 1 | 一致 |
| `orchestrator/calibrator/cli.py:52` | module の capability issuer import | 1 | 一致 |

**合成 source の行番号 pin**

以下はテスト内文字列の論理 file 名です。共通 prefix は `orchestrator/campaign/`。行番号 pin はすべて表の source 行番号と同じで、一致しています。

| 合成 source file:line | Entry | 結果 |
|---|---|---|
| `synthetic_missing_gate.py:5` | `build` | 一致 |
| `not_in_deferred_ledger.py:3` | `build` | 一致 |
| `synthetic_two_builds.py:11` | `ungated_build` | 一致 |
| `synthetic_t2155_with_name_checked.py:6` | `run` | 一致 |
| `synthetic_t2155_with_tuple_checked.py:9` | `run` | 一致 |
| `synthetic_t2520_opaque_closure.py:4` | `outer.build` | 一致 |
| `synthetic_t2520_local_fixed_shadow.py:6` | `outer.build` | 一致 |
| `synthetic_t2155_branch_local.py:6` | `run` | 一致 |
| `synthetic_t2155_late_check.py:4` | `run` | 一致 |
| `synthetic_t2155_rebound.py:6` | `run` | 一致 |
| `synthetic_t2155_loop_rebound.py:8` | `run` | 一致 |
| `synthetic_t2155_conditional_alias.py:6` | `run` | 一致 |
| `synthetic_t2155_short_circuit.py:5` | `run` | 一致 |
| `synthetic_t2155_fake_method.py:9` | `run` | 一致 |
| `synthetic_t2155_local_helper_shadow.py:7` | `run` | 一致 |
| `synthetic_t2155_helper_arg_shadow.py:5` | `run` | 一致 |
| `synthetic_t2155_default_walrus.py:7` | `run` | 一致 |
| `synthetic_t2155_guard_walrus.py:7` | `run` | 一致 |
| `synthetic_t2155_expression_walrus.py:5` | `run` | 一致 |
| `synthetic_t2155_unrelated_default.py:7` | `run` | 一致 |
| `synthetic_t2155_read_only_guard.py:7` | `run` | 一致 |
| `synthetic_t2155_class_global_helper.py:10` | `run` | 一致 |
| `synthetic_t2155_nonlocal_checked.py:9` | `run` | 一致 |
| `synthetic_t2155_star_import.py:6` | `run` | 一致 |
| `synthetic_t2155_lambda_default.py:6` | `run` | 一致 |
| `synthetic_t2155_false_guard_exit.py:8` | `run` | 一致 |
| `synthetic_t2155_false_guard_next.py:9` | `run` | 一致 |
| `synthetic_t2155_unrelated_declarations.py:13` | `run` | 一致 |
| `synthetic_t2155_ungated_name.py:4` | `run` | 一致 |
| `synthetic_t2155_ungated_tuple.py:4` | `run` | 一致 |
| `synthetic_dynamic_genome.py:3` | `build` | 一致 |
| `synthetic_wrong_macro_gate.py:10` | `build` | 一致 |

合成起動本数も、`campaign/nested/driver.py` の `launch` は **3**（3・4・5 行）、`campaign/unreviewed.py` の `launch` は **1**（3 行）で実走成功しています。

`future_build:99999` は実在 source の pin ではなく、「同じ file の未登録 sink を台帳が受理しない」ことを確認する負例です。その拒否テストも成功しました。