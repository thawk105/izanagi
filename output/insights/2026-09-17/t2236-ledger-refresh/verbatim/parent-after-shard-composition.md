# after 走 (session 895f300ad85be224d08c276069903643、tip 31c92c151、refresh 後台帳) の shard 別構成

台帳予測 = refresh 後台帳の値の和 (未登録は consumer と同じ 1.0 秒)。実測 = JUnit time の和。group = report.json の group_to_workers の key。

## shard-0: files=25 nodes=3908 台帳予測=7502 秒 実測直列和=8569 秒 groups=['campaign-repository-scan', 'real-repo', 's8c-predicate-snapshot', 's8c-preregistration-candidate']

| 台帳予測 | 実測 | node | file |
|---|---|---|---|
| 2804 | 3131 | 147 | `orchestrator/tests/test_s8b_oracle_driver.py` |
| 2368 | 2373 | 528 | `orchestrator/tests/test_s8b_floor_campaign.py` |
| 550 | 767 | 51 | `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` |
| 483 | 524 | 643 | `orchestrator/tests/test_codex_reasoning_ab.py` |
| 331 | 327 | 218 | `orchestrator/tests/test_s8c_preregistration_predicates.py` |
| 170 | 268 | 95 | `orchestrator/tests/test_real_repo_serialization.py` |
| 168 | 189 | 59 | `orchestrator/tests/test_s1_known_axes_freeze.py` |
| 152 | 219 | 418 | `orchestrator/tests/test_campaign.py` |
| 115 | 166 | 414 | `orchestrator/tests/test_p3_s4_loop.py` |
| 99 | 37 | 58 | `orchestrator/tests/test_p3_s4_loop_sort.py` |
| 79 | 348 | 104 | `orchestrator/tests/test_sort_swo_oracle.py` |
| 56 | 51 | 79 | `orchestrator/tests/test_acceptance_schedule_order.py` |

## shard-1: files=166 nodes=11415 台帳予測=5328 秒 実測直列和=4839 秒 groups=['p3-b4-material-report']

| 台帳予測 | 実測 | node | file |
|---|---|---|---|
| 832 | 823 | 50 | `orchestrator/tests/test_p3_b4_producer_auth_experiment.py` |
| 544 | 238 | 216 | `orchestrator/tests/test_run_tests_preflight.py` |
| 400 | 423 | 282 | `orchestrator/tests/test_t126_pegasus_tools.py` |
| 382 | 362 | 50 | `orchestrator/tests/test_p3_b4_raw_record_producer.py` |
| 309 | 246 | 295 | `orchestrator/tests/test_trial_registry.py` |
| 276 | 237 | 462 | `orchestrator/tests/test_check_ai_provenance.py` |
| 246 | 225 | 577 | `orchestrator/tests/test_check_docs.py` |
| 206 | 154 | 295 | `orchestrator/tests/test_t2187_adaptive_const_probe.py` |
| 178 | 171 | 50 | `orchestrator/tests/test_p3_b4_material_report.py` |
| 158 | 188 | 79 | `orchestrator/tests/test_dynamic_backoff_transitions.py` |
| 141 | 69 | 72 | `orchestrator/tests/test_p3_b4_closed_critic.py` |
| 128 | 127 | 378 | `orchestrator/tests/test_dev_wave_wait.py` |

## shard-2: files=166 nodes=9274 台帳予測=5328 秒 実測直列和=4799 秒 groups=['dev-waves-runtime']

| 台帳予測 | 実測 | node | file |
|---|---|---|---|
| 945 | 1054 | 189 | `orchestrator/tests/test_s8b_ratified_verify.py` |
| 492 | 438 | 164 | `orchestrator/tests/test_s8b_holdout_freeze.py` |
| 405 | 349 | 82 | `orchestrator/tests/test_s8b_ratified_freeze.py` |
| 370 | 27 | 140 | `orchestrator/tests/test_critic.py` |
| 346 | 415 | 25 | `orchestrator/tests/test_t139_submission_path.py` |
| 274 | 314 | 58 | `orchestrator/tests/test_t338_submission_gate_unit5.py` |
| 225 | 269 | 47 | `orchestrator/tests/test_ccbench_spawn_sites.py` |
| 178 | 137 | 321 | `orchestrator/tests/test_dev_wave_land.py` |
| 170 | 186 | 121 | `orchestrator/tests/test_related_work_search.py` |
| 142 | 135 | 269 | `orchestrator/tests/test_s8b_oracle_report.py` |
| 132 | 33 | 139 | `orchestrator/tests/test_s1_direct_comparison.py` |
| 125 | 57 | 166 | `orchestrator/tests/test_t316_sandbox_probe.py` |
