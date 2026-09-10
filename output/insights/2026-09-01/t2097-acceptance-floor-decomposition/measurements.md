# 親が段 1 で実測した生の出力 (再現コマンドつき)

## A. 所要台帳の上位単体 node と @suffix
```
nodes: 17639 total: 9610.0

=== top 25 single nodes ===
  140.00  orchestrator/tests/test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications
   94.00  orchestrator/tests/test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment
   79.00  orchestrator/tests/test_s8b_floor_campaign.py::test_real_output_snapshot_excludes_git_ignored_real_output_changes
   75.00  orchestrator/tests/test_trial_registry.py::test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads
   60.00  orchestrator/tests/test_dev_wave_wait.py::test_producer_waiter_kill_requires_later_check_only_receipt[sigkill]
   60.00  orchestrator/tests/test_dev_wave_wait.py::test_producer_waiter_kill_requires_later_check_only_receipt[sigterm]
   56.00  orchestrator/tests/test_s8b_floor_campaign.py::test_official_resume_rejects_renamed_run_dir
   55.00  orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]
   53.00  orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5
   52.00  orchestrator/tests/test_s8b_floor_campaign.py::test_pilot_resume_rejects_launch_certificate_contamination[campaign-key]
   52.00  orchestrator/tests/test_s8b_floor_campaign.py::test_pilot_resume_rejects_launch_certificate_contamination[launch-start]
   50.00  orchestrator/tests/test_s8b_floor_campaign.py::test_official_resume_rejects_certificate_time_not_bound_to_run_id
   50.00  orchestrator/tests/test_s8b_floor_campaign.py::test_official_resume_validates_certificate_and_completes
   50.00  orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes
   49.00  orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated]
   49.00  orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes]
   48.00  orchestrator/tests/test_real_repo_serialization.py::test_real_repo_writers_do_not_materialize_oracle_environment_candidates
   48.00  orchestrator/tests/test_s8b_floor_campaign.py::test_official_resume_rejects_tampered_certificate
   48.00  orchestrator/tests/test_s8b_floor_campaign.py::test_pilot_resume_rejects_launch_certificate_contamination[certificate-file]
   48.00  orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer]
   48.00  orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff]
   48.00  orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes]
   48.00  orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]
   47.00  orchestrator/tests/test_p3_autonomous_workload_trial.py::test_three_workload_build_positive_admission_passes_real_layer3_chain
   47.00  orchestrator/tests/test_s8b_floor_campaign.py::test_official_fresh_issues_certificate_and_binds_wall_ledger

=== nodeid @suffixes === [('group]', 2), (']', 1), ('\\u76f4\\u5217]', 1), ('\\u4f8b]]', 1), ('literal]]', 1), (' SENTINEL_UNEXPECTED_TOKEN]]', 1), ('second]', 1), ('two]]', 1), ('literal]', 1), (' SENTINEL_UNEXPECTED_TOKEN]', 1), ('\\n-int outside = 0;-EVOLVE-BLOCK \\u9818\\u57df\\u5916\\u306e\\u884c\\u306e\\u524a\\u9664\\u30fb\\u6539\\u5909\\u3092\\u691c\\u51fa]', 1), ('\\n-// EVOLVE-BLOCK-BEGIN fixture-\\u30d5\\u30ec\\u30fc\\u30e0\\u884c (\\u30de\\u30fc\\u30ab\\u30fc/#if/#else/#endif/stock \\u679d) \\u306e\\u524a\\u9664\\u30fb\\u6539\\u5909\\u3092\\u691c\\u51fa]', 1), ('\\n int hole = 0;\\n+int bad = 1; /* comment */-hole \\u5185\\u306b\\u7981\\u6b62\\u30b3\\u30e1\\u30f3\\u30c8 delimiter byte \\u3092\\u691c\\u51fa (\\u6587\\u5b57\\u5217\\u30fbraw string \\u5185\\u3082\\u4fdd\\u5b88\\u7684\\u306b\\u62d2\\u5426)]', 1), ('\\n int hole = 0;\\n+int bad = 1; // comment-hole \\u5185\\u306b\\u7981\\u6b62\\u30b3\\u30e1\\u30f3\\u30c8 delimiter byte \\u3092\\u691c\\u51fa (\\u6587\\u5b57\\u5217\\u30fbraw string \\u5185\\u3082\\u4fdd\\u5b88\\u7684\\u306b\\u62d2\\u5426)]', 1), ('sign]', 1), ('staticmethod\\n    def run_path(path):\\n        return path\\nrunpy.run_path(__file__)\\n]', 1), ('args.rsp]', 1), ('real-repo', 1)]
```
## B. xdist group ごとの作業単位合計 (台帳)
```
group                               funcs  nodes     sum_s   max_s
campaign-repository-scan                6      6       0.0     0.0
dev-waves-runtime                      11     22      16.0     2.0
s8c-predicate-snapshot                  3      3      52.0    33.0
s8c-preregistration-candidate           5      5      83.5    34.0

real-repo process-memo unit sum = 0.0 s over 4 funcs
total work = 9610.0 s ; work/(48*3) = 66.7 s
```
## C. real-repo の資源別 cohort (台帳)
```
cohort                                    funcs  nodes     sum_s  maxfn_s
parent=None ccbench=read                      6      6       3.6      3.5
parent=None ccbench=write                     1      1       0.2      0.2
parent=read ccbench=None                     34     35      78.5     14.0
parent=read ccbench=read                     52     54     221.6     94.0
parent=read ccbench=write                     3      3       0.0      0.0

resource nodes: 96 local-only: 2
ccbench writers: ['test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration', 'test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration', 'test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2', 'test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding']
    (0.0, 1) test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration
    (0.0, 1) test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration
    (0.0, 1) test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2
    (0.19, 1) test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding

real-repo resource-node total = 303.9 s
```
## D. 実走 junit の単体所要 (2026-09-01 08:15 の受入全走)
```

=== shard-0: cases=6405 sum=5816.6s  max=126.1s
     126.13  orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]
     122.38  orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5
     118.49  orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes]
     117.81  orchestrator.tests.test_s8b_oracle_driver::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated]
     116.42  orchestrator.tests.test_s8b_oracle_driver::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff]
     116.37  orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]
     116.03  orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes]
     115.67  orchestrator.tests.test_s8b_oracle_driver::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28

=== shard-1: cases=6405 sum=4687.8s  max=68.4s
      68.38  orchestrator.tests.test_p3_b4_raw_record_producer::test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings
      66.94  orchestrator.tests.test_p3_b4_raw_record_producer::test_positive_201_block_all_terminal_records_absent
      60.17  orchestrator.tests.test_dev_wave_wait::test_producer_waiter_kill_requires_later_check_only_receipt[sigterm]
      60.16  orchestrator.tests.test_dev_wave_wait::test_producer_waiter_kill_requires_later_check_only_receipt[sigkill]
      58.13  orchestrator.tests.test_login_headroom::test_ceiling_numeric_literal_occurs_only_in_login_headroom_module
      57.88  orchestrator.tests.test_trial_registry::test_t822_acceptance_reports_changed_layer3_snapshot_identity
      57.82  orchestrator.tests.test_trial_registry::test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads
      30.33  orchestrator.tests.test_s8b_holdout_freeze::test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility[min-to-max]

=== shard-2: cases=6405 sum=2044.5s  max=73.2s
      73.19  orchestrator.tests.test_p3_autonomous_workload_trial::test_role_sink_bytes_vary_only_at_declared_declassifications
      32.80  orchestrator.tests.test_p3_autonomous_workload_trial::test_three_workload_build_positive_admission_passes_real_layer3_chain
      32.27  orchestrator.tests.test_pytest_collection_config::test_cleanup_collection_positive_control_with_empty_production_exclusions
      32.23  orchestrator.tests.test_check_ai_provenance::test_provenance_headroom_short_queue_unavailable_cap_oom_stops
      32.22  orchestrator.tests.test_run_tests_preflight::test_headroom_short_queue_unavailable_cap_oom_stops_without_dispatch
      25.49  orchestrator.tests.test_t338_submission_gate_unit5::test_conformance_vector_is_executed[writer_publish_sealed_authority]
      23.63  orchestrator.tests.test_t338_submission_gate_unit5::test_conformance_vector_is_executed[negative-6.10-create-only-existing]
      22.82  orchestrator.tests.test_check_subprocess_bytecode_guard::test_real_repo_clean

=== ALL shards: cases=19215 sum=12548.9s
     126.13  orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]
     122.38  orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5
     118.49  orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes]
     117.81  orchestrator.tests.test_s8b_oracle_driver::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated]
     116.42  orchestrator.tests.test_s8b_oracle_driver::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff]
     116.37  orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]
     116.03  orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes]
     115.67  orchestrator.tests.test_s8b_oracle_driver::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28
     115.36  orchestrator.tests.test_s8b_oracle_driver::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer]
     113.69  orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5
     100.20  orchestrator.tests.test_s8b_floor_campaign::test_official_build_failure_leaves_durable_launch_start
      97.68  orchestrator.tests.test_s8b_floor_campaign::test_official_fresh_issues_certificate_and_binds_wall_ledger
      96.13  orchestrator.tests.test_s8b_floor_campaign::test_official_resume_validates_certificate_and_completes
      95.64  orchestrator.tests.test_s8b_floor_campaign::test_pilot_resume_rejects_launch_certificate_contamination[certificate-file]
      95.50  orchestrator.tests.test_s8b_floor_campaign::test_official_scan_rejection_has_zero_filesystem_side_effects
```

## E. 実走 shard の pytest wall と scheduler (同じ受入全走)
```
-- shard-0
6327 passed, 78 skipped in 213.91s
-- shard-1
6399 passed, 6 skipped in 176.01s
-- shard-2
6397 passed, 8 skipped, 3 warnings in 130.63s
shard 0 effective_scheduler= loadgroup shard_count= 3 group_to_workers= {'campaign-repository-scan': 1, 'real-repo': 39, 's8c-predicate-snapshot': 1, 's8c-preregistration-candidate': 1}
shard 1 effective_scheduler= loadgroup shard_count= 3 group_to_workers= {'dev-waves-runtime': 1}
shard 2 effective_scheduler= loadgroup shard_count= 3 group_to_workers= {}
```

artifact root: /work/1/SFC/tanab/.izanagi-acceptance-shards/349543d56cdc8d141798abb3626121e9

## F. 14 セッション横断の床の分解 (親が段 1 の後に追加実測)

resid = wall - max(max1, busy/48)
```
session    shard      wall_s    busy_s  busy/48   max1_s    resid
7ac4faab   shard-0     226.0    6658.1    138.7    144.1     81.9
7ac4faab   shard-1     166.7    5103.9    106.3     85.1     60.3
7ac4faab   shard-2     134.0    2211.8     46.1     76.2     57.8

349543d5   shard-0     213.9    5816.6    121.2    126.1     87.8
349543d5   shard-1     176.0    4687.8     97.7     68.4     78.3
349543d5   shard-2     130.6    2044.5     42.6     73.2     57.4

6f39928e   shard-0     202.5    5756.8    119.9    123.6     78.9
6f39928e   shard-1     137.5    3740.2     77.9     60.2     59.5
6f39928e   shard-2     125.8    1794.7     37.4     63.3     62.5

690c10ec   shard-0     233.3    6936.8    144.5    144.2     88.8
690c10ec   shard-1     141.8    3779.8     78.7     60.2     63.1
690c10ec   shard-2     132.9    2032.7     42.3     70.1     62.9

4524841d   shard-0     212.3    5751.3    119.8    125.5     86.8
4524841d   shard-1     144.5    3923.5     81.7     60.2     62.7
4524841d   shard-2     123.6    1649.9     34.4     60.5     63.1

b6b39445   shard-0     223.9    5567.2    116.0    119.4    104.5
b6b39445   shard-1     140.5    3891.0     81.1     60.2     59.4
b6b39445   shard-2     132.1    1760.3     36.7     69.5     62.6

bd617d36   shard-0     195.8    5514.1    114.9    118.6     77.2
bd617d36   shard-1     140.7    3246.5     67.6     60.2     73.0
bd617d36   shard-2     136.6    2125.5     44.3     69.7     67.0

92a64a50   shard-0     210.0    5897.8    122.9    132.8     77.2
92a64a50   shard-1     140.9    3903.6     81.3     60.2     59.5
92a64a50   shard-2     123.5    1616.1     33.7     65.9     57.7

68f13f48   shard-0     226.8    6243.0    130.1    134.4     92.4
68f13f48   shard-1     130.0    3283.1     68.4     60.2     61.6
68f13f48   shard-2     132.7    2050.1     42.7     65.3     67.3

63bcb314   shard-0     212.8    5758.4    120.0    126.0     86.8
63bcb314   shard-1     215.4    7475.7    155.7    153.9     59.6
63bcb314   shard-2     131.9    2154.5     44.9     64.5     67.4

ab716aea   shard-0     216.7    6317.0    131.6    138.4     78.3
ab716aea   shard-1     188.6    5335.5    111.2     86.1     77.4
ab716aea   shard-2     199.7    3610.5     75.2    135.7     64.0

3125bcc7   shard-0     286.4    9159.9    190.8    205.2     81.1
3125bcc7   shard-1     133.9    3621.0     75.4     60.2     58.5
3125bcc7   shard-2     139.8    2373.6     49.4     71.9     67.8

8410a1ac   shard-0     220.9    6554.2    136.5    143.8     77.0
8410a1ac   shard-1     134.9    3209.8     66.9     60.2     68.0
8410a1ac   shard-2     136.6    2128.7     44.3     70.1     66.5

dd911f21   shard-0     310.3   10192.4    212.3    219.3     91.0
dd911f21   shard-1     141.5    3899.3     81.2     60.2     60.2
dd911f21   shard-2     124.8    1683.0     35.1     67.7     57.2

```

観察 1: 残差は shard-2 (排他 group がゼロの shard) でも 57-68 秒あり、全 shard でほぼ一定である。
観察 2: shard-0 では max1 と busy/48 がほぼ等しく推移する (118.6/114.9 から 219.3/212.3 まで)。

## G. real-repo 排他閉包が shard-0 の仕事量に占める割合 (実走 junit x access map)
```

=== shard-0: busy=5816.6s  real-repo=162.5s (2.8%)  最長 real-repo 単体=34.7s
    test_real_repo_serialization.py::test_t080_import_temp_environment_fails_closed_for_foreign_module
    parent=read ccbench=None              130.7s
    parent=read ccbench=read               27.8s
    parent=None ccbench=read                3.8s
    parent=None ccbench=write               0.2s
    parent=read ccbench=write               0.0s

=== shard-1: busy=4687.8s  real-repo=0.0s (0.0%)  最長 real-repo 単体=0.0s
    

=== shard-2: busy=2044.5s  real-repo=0.0s (0.0%)  最長 real-repo 単体=0.0s
    
```

観察 3: real-repo group は 1 component として shard-0 に固定されているが、shard-0 の総仕事量
5816.6 秒のうち 162.5 秒 (2.8%) しか占めない。最長の real-repo 単体は 34.7 秒で、shard の最長単体
126.1 秒よりはるかに小さい。したがって component を shard 間へ割り直しても busy/48 は
121.2 秒から約 119 秒にしか動かない。

観察 4 (親の留保): 観察 2 の相関は因果を示さない。shard 割付は node 集合が同じなら決定的なので、
session 間で busy が動くのは所要そのものが動くからであり、busy と max1 が一緒に動くのは
「その日の機械が遅い」という共通原因で説明できる。shard-0 の負荷を減らせば max1 が縮むという
主張の根拠にはならない。

## H. 到達可能な makespan の反実仮想 (LPT で下界を出した)

shard 割付の閉包は tools/acceptance_shards.py:321 _components() が作る。頂点は file と group で、
group を共有する file だけが union される。したがって group を持たない file は単独 component になるが、
**その file の全 node が 1 shard へ束ねられる**。重みは所要ではなく node 数 (weight = len(nodeids))。
REAL_REPO_GROUP_CONFLICT_EDGES (acceptance_shards.py:77) が 4 group を相互に conflict と宣言し、
1 component へ畳んで 1 shard に固定する。
```
総仕事量 12548.9s / file 数 308 / node 数 19215

最長単体 node = 126.1s
B) file 粒度で完璧に割った最悪 shard busy = 4183.0s -> /48 = 87.1s
C) node 粒度で完璧に割った最悪 shard busy = 4183.0s -> /48 = 87.1s
   均等割の下界 total/K/W = 87.1s

床(pytest wall) = 残差 + max(最長単体, busy/48)
   現行 shard-0       busy/48=  121.2s  max(.,126.1)=  126.1s  +残差80 -> 206.1s
   B file粒度理想       busy/48=   87.1s  max(.,126.1)=  126.1s  +残差80 -> 206.1s
   C node粒度理想       busy/48=   87.1s  max(.,126.1)=  126.1s  +残差80 -> 206.1s
```

観察 5: file 粒度で完璧に割っても node 粒度で完璧に割っても、到達できる最悪 shard の busy は
同じ 4183.0 秒 (= total/3) である。/48 すると 87.1 秒で、最長単体 126.1 秒を下回る。
したがって **閉包を file から node へ細分化しても makespan は 1 秒も動かない**。
割付でも閉包でも取れる余地は現行 213.9 秒に対して合計 7.8 秒 (3.6%) しかなく、
その 7.8 秒も file 粒度の所要重み (D1019 が却下済みの軸) で既に取れる。

## I. worker への詰め込みまで含めた下界 (段 3 投入後に親が追加計算した。段 3 の子はこれを見ていない)
```
集合                    busy  busy/48    max1    LPT48
shard-0             5816.6    121.2   126.1    126.1
shard-1             4687.8     97.7    68.4     97.7
shard-2             2044.5     42.6    73.2     73.2

--- node 粒度で 3 shard へ完璧に割った場合 ---
shard-0: busy=   4183.0 busy/48=   87.1 max1= 126.1 LPT48=  126.1
shard-1: busy=   4183.0 busy/48=   87.1 max1= 122.4 LPT48=  122.4
shard-2: busy=   4183.0 busy/48=   87.1 max1= 118.5 LPT48=  118.5

最悪 shard の worker occupancy: 現行 shard-0 LPT48 = 126.1s -> 理想 126.1s (差 0.0s)
実走の shard-0 pytest wall = 213.9s、段 2 が読んだ最大 worker occupancy = 135.68s
=> 固定費 = 213.9 - 135.68 = 78.2s
=> 理想時の wall 予測 = 126.1 + 78.2 = 204.4s  (固定費が負荷非依存だと仮定した場合)
```

観察 6: shard-0 を 48 worker へ完璧に詰めた LPT48 は 126.1 秒で、最長単体 node と一致する。
実走の最大 worker occupancy は 135.68 秒だったので、詰め込みの余地は 9.6 秒しかない。
観察 7: node 粒度で 3 shard へ完璧に割り直しても、最悪 shard の LPT48 は 126.1 秒のまま動かない。
つまり **shard 間の割付でも worker 間の詰め込みでも、最悪 shard の occupancy は 126.1 秒より下がらない**。
観察 8: wall = 固定費 + 最大 worker occupancy と分解すると、固定費は shard-0 が 78.2 秒、
shard-1 が 56.3 秒、shard-2 が 56.4 秒。shard-0 だけ約 21.9 秒多い。real-repo component が
shard-0 にしか無いので、controller prewarm がこの差の候補になる。ただし prewarm は
どの shard が real-repo を持っても払う費用であり、割り直しで消える費用ではない。

## J. shard component の実測 (段 2 の主張を親が独立に確かめた)
```
component file 数 = 23
component の node 数 = 3405 (うち real-repo access map 掲載 = 95)
component の実走所要合計 = 4187.6s (うち access map 掲載 = 162.5s)
component の最長単体 = 126.1s

shard-0 の busy 5816.6s に対する component の割合 = 72.0%
component を外した後の shard-0 busy = 1629.0s -> /48 = 33.9s
component だけを 48 worker へ詰めた LPT48 = 126.1s
```

観察 9: 段 2 の主張は正しい。component は 23 file・3405 node で、shard-0 の仕事量の 72.0% を占める。
しかしそのうち real-repo access map に載るのは 95 node・162.5 秒 (3.9%) だけで、残りは
同じ file に居るというだけで shard-0 に拘束されている。
観察 10: それでも component だけを 48 worker へ詰めた LPT48 は 126.1 秒で、最長単体と一致する。
最長単体 126.1 秒の node 自身が access map 外 (file に引きずられて入っている) であり、
どこへ動かしてもその shard の occupancy 下界を 126.1 秒にする。
