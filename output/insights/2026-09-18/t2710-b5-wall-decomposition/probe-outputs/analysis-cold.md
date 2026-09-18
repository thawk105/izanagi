## 対象と定義

replica shard-0 の同一 tip 反復。受入証跡ではない。model は下限参考値。

走数 10、採用 9。中央値は各走を分解した後、指標別に計算。

W=JUnit testsuite、L=JUnit testcase 最大、O=phase 合算最大、F=W−O、P=O−L、D=全 phase 合算。

## shard 表

| condition | run | host | ordinal | W | O | O_production | O_difference | F | L | longest_node | P | longest_on_busy | D | mean_load | busy_worker | busy_count | terminal | outer_wall | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | job2-01-A | bnode016 | 1 | 414.7 | 285.2 | 285.2 | -0.0 | 129.4 | 265.3 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 19.9 | True | 8904.5 | 185.5 | gw5 | 2 | {"selected": 3938, "executed_selected": 3938, "finished": 3938, "failed": 0, "skipped": 53, "rc": 0} | 415.9 | 採用 |
| B | job2-02-B | bnode016 | 2 | 362.6 | 232.1 | 232.1 | -0.0 | 130.5 | 232.1 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 0.0 | True | 7740.5 | 161.3 | gw5 | 2 | {"selected": 3938, "executed_selected": 3938, "finished": 3938, "failed": 0, "skipped": 53, "rc": 0} | 363.9 | 採用 |
| C | job2-03-C | bnode016 | 3 | 412.0 | 283.8 | 283.8 | -0.0 | 128.2 | 263.4 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | 20.4 | True | 8909.2 | 185.6 | gw4 | 2 | {"selected": 3938, "executed_selected": 3937, "finished": 3937, "failed": 0, "skipped": 53, "rc": 0} | 413.3 | 採用 |
| B | job3-01-B | bnode021 | 1 | 345.6 | 217.1 | 217.1 | -0.0 | 128.5 | 217.1 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | -0.0 | True | 7433.9 | 154.9 | gw5 | 2 | {"selected": 3938, "executed_selected": 3938, "finished": 3938, "failed": 0, "skipped": 53, "rc": 0} | 346.9 | 採用 |
| C | job3-02-C | bnode021 | 2 | 417.8 | 288.8 | 288.8 | 0.0 | 129.0 | 268.8 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | 20.0 | True | 9226.5 | 192.2 | gw4 | 2 | {"selected": 3938, "executed_selected": 3937, "finished": 3937, "failed": 0, "skipped": 53, "rc": 0} | 419.1 | 採用 |
| A | job3-03-A | bnode021 | 3 | 410.7 | 281.4 | 281.4 | -0.0 | 129.3 | 261.5 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 20.0 | True | 8691.0 | 181.1 | gw5 | 2 | {"selected": 3938, "executed_selected": 3938, "finished": 3938, "failed": 0, "skipped": 53, "rc": 0} | 412.0 | 採用 |
| C | job4-01-C | bnode017 | 1 | 438.9 | 309.8 | 309.8 | 0.0 | 129.1 | 289.8 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | 20.0 | True | 10005.6 | 208.4 | gw4 | 2 | {"selected": 3938, "executed_selected": 3937, "finished": 3937, "failed": 0, "skipped": 53, "rc": 0} | 440.3 | 採用 |
| A | job4-02-A | bnode017 | 2 | 435.3 | 306.5 | 306.5 | 0.0 | 128.7 | 286.6 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 19.9 | True | 9730.5 | 202.7 | gw5 | 2 | {"selected": 3938, "executed_selected": 3938, "finished": 3938, "failed": 0, "skipped": 53, "rc": 0} | 436.6 | 採用 |
| B | job4-03-B | bnode017 | 3 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 517.6 | 除外 (rc != 0; controller exitstatus != 0; FileNotFoundError(2, 'No such file or directory')) |
| B | job5-01-B | bnode014 | 1 | 344.4 | 216.4 | 216.4 | -0.0 | 128.0 | 216.4 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 0.0 | True | 7559.2 | 157.5 | gw5 | 2 | {"selected": 3938, "executed_selected": 3938, "finished": 3938, "failed": 0, "skipped": 53, "rc": 0} | 345.7 | 採用 |

## job2-01-A

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 265.3 | 1789700313.0 |
| orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication | 19.9 | 1789700578.3 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw4 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 258.5 | 0.0 | 239.6 | 235.7 | 0.0 | 235.7 | 0.0 | 3.9 | [0.0, 5.2, 4.6, 4.5] | 0.0 | 4.6 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 249.2 | 0.0 | 239.4 | 235.5 | 235.5 | 0.0 | 0.0 | 3.8 | [5.3, 4.6] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw8 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 244.7 | 0.0 | 239.3 | 235.5 | 235.5 | 0.0 | 0.0 | 3.8 | [5.3, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 265.3 | 0.0 | 239.4 | 235.5 | 0.0 | 235.5 | 0.0 | 3.8 | [5.3, 4.8, 4.7, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 244.6 | 0.0 | 239.4 | 235.5 | 235.5 | 0.0 | 0.0 | 3.8 | [5.3] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw10 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 239.5 | 0.0 | 239.4 | 235.5 | 235.5 | 0.0 | 0.0 | 3.8 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw11 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 244.7 | 0.0 | 239.4 | 235.5 | 0.0 | 235.5 | 0.0 | 3.9 | [5.3] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw12 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 244.8 | 0.0 | 239.7 | 235.8 | 0.0 | 235.8 | 0.0 | 3.9 | [5.2] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw7 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 246.7 | 0.0 | 239.4 | 235.5 | 235.5 | 0.0 | 0.0 | 3.8 | [5.0] | 0.0 | 2.4 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw13 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 242.3 | 0.0 | 239.4 | 235.5 | 235.5 | 0.0 | 0.0 | 3.8 | [] | 0.0 | 2.9 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw38 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 184.1 | 0.0 | 178.6 | 176.0 | 0.0 | 176.0 | 0.0 | 2.6 | [0.0, 0.0, 0.0] | 0.0 | 5.4 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw5 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 265.3}, {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 19.9}] |
| second | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 19.9} |
| initial_second_predicted | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "nodes": 1, "nodeids": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"]} |
| initial_second_observed_matches | True |
| third_or_later | False |
| collection_matches | {"gw10": null, "gw6": null, "gw5": null, "gw4": null, "gw3": null, "gw2": null, "gw0": null, "gw16": null, "gw7": null, "gw12": null, "gw19": null, "gw24": null, "gw15": null, "gw18": null, "gw1": null, "gw9": null, "gw11": null, "gw8": null, "gw17": null, "gw20": null, "gw31": null, "gw25": null, "gw23": null, "gw33": null, "gw22": null, "gw21": null, "gw13": null, "gw14": null, "gw30": null, "gw37": null, "gw32": null, "gw26": null, "gw36": null, "gw34": null, "gw35": null, "gw29": null, "gw43": null, "gw41": null, "gw28": null, "gw27": null, "gw38": null, "gw39": null, "gw42": null, "gw46": null, "gw47": null, "gw45": null, "gw44": null, "gw40": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 120.9 |
| execution_interval | 285.3 |
| last_test_to_sessionfinish | 8.7 |
| outer_minus_junit | 1.2 |
| execution_minus_occupancy | 0.0 |
| (省略: 4830 bytes の行。原本は job dir analysis/cold/analysis.md) |
| (省略: 84057 bytes の行。原本は job dir analysis/cold/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw10": 0.0, "gw11": 0.0, "gw12": 0.0, "gw13": 0.0, "gw38": 0.0, "gw4": 0.0, "gw5": 0.0, "gw6": 0.0, "gw7": 0.0, "gw8": 0.0, "gw9": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

model

| metric | value |
|---|---|
| A_model | 394.7 |
| A_residual | 19.9 |
| assumptions | Fixed durations and F_A; lower-bound model, not implementation effect. Independent split loses same-root positive-to-mutation continuity; duplicated observed helper/setup/teardown. Build executed once in reality; both waits may recur. Session cleanup change is unmodeled. |
| L_reduce | 265.3 |
| D_reduce | 8165.9 |
| reduce_model | 394.7 |
| reduce_gain_model | -0.0 |
| d_positive | 249.5 |
| d_defect | 255.2 |
| positive_other | 0.0 |
| mutation_plus_defect_other | 2.1 |
| call_boundary_other | 0.0 |
| L_split | 258.5 |
| D_split | 9143.8 |
| split_model | 387.9 |
| split_gain_model | 6.8 |

## job2-02-B

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 232.1 | 1789700732.3 |
| orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases | 0.0 | 1789700964.4 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw4 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 225.5 | 0.0 | 206.5 | 202.2 | 0.0 | 202.2 | 0.0 | 4.3 | [0.0, 5.3, 4.6, 4.5] | 0.0 | 4.6 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 216.4 | 0.0 | 206.5 | 202.2 | 202.2 | 0.0 | 0.0 | 4.3 | [5.3, 4.6] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw8 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 211.8 | 0.0 | 206.5 | 202.2 | 202.2 | 0.0 | 0.0 | 4.3 | [5.3, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 232.1 | 0.0 | 206.5 | 202.2 | 202.2 | 0.0 | 0.0 | 4.3 | [5.3, 4.6, 4.5, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 211.8 | 0.0 | 206.5 | 202.2 | 202.2 | 0.0 | 0.0 | 4.3 | [5.3] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw10 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 206.6 | 0.0 | 206.5 | 202.2 | 202.2 | 0.0 | 0.0 | 4.3 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw11 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 211.9 | 0.0 | 206.6 | 202.3 | 0.0 | 202.3 | 0.0 | 4.3 | [5.3] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw12 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 211.9 | 0.0 | 206.7 | 202.3 | 0.0 | 202.3 | 0.0 | 4.3 | [5.2] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw7 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 213.9 | 0.0 | 206.5 | 202.2 | 0.0 | 202.2 | 0.0 | 4.3 | [4.9] | 0.0 | 2.5 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw13 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 209.5 | 0.0 | 206.5 | 202.2 | 202.2 | 0.0 | 0.0 | 4.3 | [] | 0.0 | 3.0 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw38 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 150.6 | 0.0 | 144.9 | 142.3 | 0.0 | 142.3 | 0.0 | 2.6 | [0.0, 0.0, 0.0] | 0.0 | 5.6 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw5 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 232.1}, {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases", "cost": 0.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases"], "duration": 0.0}] |
| second | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases", "cost": 0.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases"], "duration": 0.0} |
| initial_second_predicted | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases", "cost": 0.0, "nodes": 1, "nodeids": ["orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases"]} |
| initial_second_observed_matches | True |
| third_or_later | False |
| collection_matches | {"gw4": true, "gw2": true, "gw8": true, "gw5": true, "gw1": true, "gw7": true, "gw0": true, "gw3": true, "gw9": true, "gw10": true, "gw6": true, "gw12": true, "gw15": true, "gw22": true, "gw20": true, "gw24": true, "gw18": true, "gw19": true, "gw21": true, "gw16": true, "gw13": true, "gw17": true, "gw29": true, "gw28": true, "gw26": true, "gw23": true, "gw11": true, "gw14": true, "gw25": true, "gw30": true, "gw35": true, "gw40": true, "gw27": true, "gw38": true, "gw32": true, "gw36": true, "gw31": true, "gw34": true, "gw44": true, "gw39": true, "gw33": true, "gw45": true, "gw41": true, "gw46": true, "gw37": true, "gw42": true, "gw43": true, "gw47": true} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 120.2 |
| execution_interval | 234.1 |
| last_test_to_sessionfinish | 8.6 |
| outer_minus_junit | 1.3 |
| execution_minus_occupancy | 2.0 |
| (省略: 6947 bytes の行。原本は job dir analysis/cold/analysis.md) |
| (省略: 84057 bytes の行。原本は job dir analysis/cold/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw10": 0.0, "gw11": 0.0, "gw12": 0.0, "gw13": 0.0, "gw38": 0.0, "gw4": 0.0, "gw5": 0.0, "gw6": 0.0, "gw7": 0.0, "gw8": 0.0, "gw9": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

## job2-03-C

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | 263.4 | 1789701099.7 |
| orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication | 20.4 | 1789701363.2 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw4 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 263.4 | 0.0 | 244.8 | 241.3 | 0.0 | 241.3 | 0.0 | 3.5 | [0.0, 4.9, 4.6, 4.5] | 0.0 | 4.6 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 254.8 | 0.0 | 245.0 | 241.5 | 241.5 | 0.0 | 0.0 | 3.5 | [5.1, 4.7] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw7 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 250.0 | 0.0 | 245.0 | 241.5 | 241.5 | 0.0 | 0.0 | 3.5 | [5.0, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw8 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 250.0 | 0.0 | 245.0 | 241.5 | 241.5 | 0.0 | 0.0 | 3.5 | [5.0] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 245.1 | 0.0 | 245.0 | 241.5 | 0.0 | 241.5 | 0.0 | 3.5 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw10 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 249.8 | 0.0 | 244.8 | 241.3 | 0.0 | 241.3 | 0.0 | 3.5 | [5.0] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw11 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 249.8 | 0.0 | 244.9 | 241.4 | 0.0 | 241.4 | 0.0 | 3.5 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 252.1 | 0.0 | 245.0 | 241.5 | 241.5 | 0.0 | 0.0 | 3.5 | [5.0] | 0.0 | 2.1 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw12 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 247.7 | 0.0 | 245.0 | 241.5 | 241.5 | 0.0 | 0.0 | 3.5 | [] | 0.0 | 2.7 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw37 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 189.6 | 0.0 | 184.2 | 181.6 | 0.0 | 181.6 | 0.0 | 2.6 | [0.0, 0.0, 0.0] | 0.0 | 5.4 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw4 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5"], "duration": 263.4}, {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 20.4}] |
| second | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 20.4} |
| initial_second_predicted | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "nodes": 1, "nodeids": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"]} |
| initial_second_observed_matches | True |
| third_or_later | False |
| collection_matches | {"gw9": null, "gw2": null, "gw7": null, "gw5": null, "gw1": null, "gw0": null, "gw3": null, "gw8": null, "gw13": null, "gw12": null, "gw19": null, "gw4": null, "gw16": null, "gw10": null, "gw11": null, "gw6": null, "gw20": null, "gw17": null, "gw18": null, "gw29": null, "gw15": null, "gw22": null, "gw14": null, "gw21": null, "gw23": null, "gw26": null, "gw30": null, "gw31": null, "gw24": null, "gw27": null, "gw25": null, "gw36": null, "gw34": null, "gw39": null, "gw32": null, "gw37": null, "gw43": null, "gw41": null, "gw38": null, "gw44": null, "gw35": null, "gw40": null, "gw28": null, "gw45": null, "gw46": null, "gw33": null, "gw47": null, "gw42": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 119.7 |
| execution_interval | 283.8 |
| last_test_to_sessionfinish | 8.7 |
| outer_minus_junit | 1.3 |
| execution_minus_occupancy | 0.0 |
| (省略: 4392 bytes の行。原本は job dir analysis/cold/analysis.md) |
| (省略: 84056 bytes の行。原本は job dir analysis/cold/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw10": 0.0, "gw11": 0.0, "gw12": 0.0, "gw37": 0.0, "gw4": 0.0, "gw5": 0.0, "gw6": 0.0, "gw7": 0.0, "gw8": 0.0, "gw9": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

## job3-01-B

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 217.1 | 1789701560.8 |
| orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases | 0.0 | 1789701777.8 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw4 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 210.6 | 0.0 | 191.8 | 187.7 | 0.0 | 187.7 | 0.0 | 4.1 | [0.0, 5.1, 4.6, 4.5] | 0.0 | 4.6 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 201.5 | 0.0 | 191.8 | 187.8 | 187.8 | 0.0 | 0.0 | 4.0 | [5.1, 4.6] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw8 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 196.9 | 0.0 | 191.8 | 187.8 | 187.8 | 0.0 | 0.0 | 4.0 | [5.1, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 217.1 | 0.0 | 191.7 | 187.8 | 187.8 | 0.0 | 0.0 | 3.9 | [5.1, 4.6, 4.5, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 196.9 | 0.0 | 191.8 | 187.8 | 187.8 | 0.0 | 0.0 | 4.0 | [5.2] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw10 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 191.9 | 0.0 | 191.8 | 187.8 | 187.8 | 0.0 | 0.0 | 4.0 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw11 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 196.9 | 0.0 | 191.8 | 187.7 | 0.0 | 187.7 | 0.0 | 4.1 | [5.1] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw12 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 196.8 | 0.0 | 191.7 | 187.6 | 0.0 | 187.6 | 0.0 | 4.0 | [5.1] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw7 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 199.0 | 0.0 | 191.8 | 187.8 | 0.0 | 187.8 | 0.0 | 4.0 | [4.9] | 0.0 | 2.3 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw13 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 194.7 | 0.0 | 191.9 | 187.8 | 187.8 | 0.0 | 0.0 | 4.1 | [] | 0.0 | 2.8 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw38 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 135.9 | 0.0 | 130.4 | 127.8 | 0.0 | 127.8 | 0.0 | 2.6 | [0.0, 0.0, 0.0] | 0.0 | 5.5 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw5 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 217.1}, {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases", "cost": 0.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases"], "duration": 0.0}] |
| second | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases", "cost": 0.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases"], "duration": 0.0} |
| initial_second_predicted | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases", "cost": 0.0, "nodes": 1, "nodeids": ["orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases"]} |
| initial_second_observed_matches | True |
| third_or_later | False |
| collection_matches | {"gw3": true, "gw2": true, "gw7": true, "gw8": true, "gw9": true, "gw5": true, "gw6": true, "gw1": true, "gw14": true, "gw4": true, "gw10": true, "gw0": true, "gw11": true, "gw15": true, "gw12": true, "gw19": true, "gw17": true, "gw16": true, "gw13": true, "gw20": true, "gw23": true, "gw28": true, "gw22": true, "gw29": true, "gw33": true, "gw26": true, "gw21": true, "gw31": true, "gw25": true, "gw24": true, "gw27": true, "gw18": true, "gw32": true, "gw35": true, "gw30": true, "gw36": true, "gw38": true, "gw34": true, "gw41": true, "gw42": true, "gw40": true, "gw37": true, "gw39": true, "gw46": true, "gw44": true, "gw45": true, "gw43": true, "gw47": true} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 120.2 |
| execution_interval | 217.1 |
| last_test_to_sessionfinish | 8.5 |
| outer_minus_junit | 1.3 |
| execution_minus_occupancy | 0.0 |
| (省略: 4830 bytes の行。原本は job dir analysis/cold/analysis.md) |
| (省略: 84057 bytes の行。原本は job dir analysis/cold/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw10": 0.0, "gw11": 0.0, "gw12": 0.0, "gw13": 0.0, "gw38": 0.0, "gw4": 0.0, "gw5": 0.0, "gw6": 0.0, "gw7": 0.0, "gw8": 0.0, "gw9": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

## job3-02-C

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | 268.8 | 1789701912.2 |
| orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication | 20.0 | 1789702181.1 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw4 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 268.8 | 0.0 | 250.2 | 246.6 | 0.0 | 246.6 | 0.0 | 3.6 | [0.0, 4.9, 4.6, 4.5] | 0.0 | 4.6 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 259.7 | 0.0 | 250.2 | 246.6 | 246.6 | 0.0 | 0.0 | 3.5 | [4.9, 4.6] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw7 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 255.1 | 0.0 | 250.2 | 246.6 | 246.6 | 0.0 | 0.0 | 3.5 | [5.0, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw8 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 255.1 | 0.0 | 250.2 | 246.6 | 246.6 | 0.0 | 0.0 | 3.5 | [5.0] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 250.2 | 0.0 | 250.2 | 246.6 | 246.6 | 0.0 | 0.0 | 3.5 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw10 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 255.3 | 0.0 | 250.4 | 246.9 | 0.0 | 246.9 | 0.0 | 3.5 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw11 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 255.3 | 0.0 | 250.3 | 246.8 | 0.0 | 246.8 | 0.0 | 3.5 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 257.2 | 0.0 | 250.2 | 246.6 | 246.6 | 0.0 | 0.0 | 3.5 | [4.9] | 0.0 | 2.1 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw12 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 252.9 | 0.0 | 250.2 | 246.6 | 0.0 | 246.6 | 0.0 | 3.5 | [] | 0.0 | 2.7 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw37 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 195.4 | 0.0 | 189.5 | 186.9 | 0.0 | 186.9 | 0.0 | 2.6 | [0.0, 0.0, 0.0] | 0.0 | 5.8 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw4 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5"], "duration": 268.8}, {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 20.0}] |
| second | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 20.0} |
| initial_second_predicted | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "nodes": 1, "nodeids": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"]} |
| initial_second_observed_matches | True |
| third_or_later | False |
| collection_matches | {"gw0": null, "gw1": null, "gw2": null, "gw5": null, "gw6": null, "gw7": null, "gw3": null, "gw8": null, "gw10": null, "gw4": null, "gw9": null, "gw14": null, "gw17": null, "gw12": null, "gw11": null, "gw19": null, "gw13": null, "gw28": null, "gw18": null, "gw22": null, "gw15": null, "gw20": null, "gw23": null, "gw16": null, "gw27": null, "gw24": null, "gw29": null, "gw21": null, "gw26": null, "gw34": null, "gw32": null, "gw30": null, "gw31": null, "gw35": null, "gw36": null, "gw41": null, "gw40": null, "gw39": null, "gw25": null, "gw37": null, "gw33": null, "gw42": null, "gw45": null, "gw44": null, "gw47": null, "gw43": null, "gw38": null, "gw46": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 120.6 |
| execution_interval | 288.8 |
| last_test_to_sessionfinish | 8.7 |
| outer_minus_junit | 1.2 |
| execution_minus_occupancy | 0.0 |
| (省略: 4392 bytes の行。原本は job dir analysis/cold/analysis.md) |
| (省略: 84056 bytes の行。原本は job dir analysis/cold/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw10": 0.0, "gw11": 0.0, "gw12": 0.0, "gw37": 0.0, "gw4": 0.0, "gw5": 0.0, "gw6": 0.0, "gw7": 0.0, "gw8": 0.0, "gw9": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

## job3-03-A

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 261.5 | 1789702335.4 |
| orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication | 20.0 | 1789702596.9 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw4 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 254.7 | 0.0 | 235.7 | 231.9 | 0.0 | 231.9 | 0.0 | 3.8 | [0.0, 5.2, 4.7, 4.5] | 0.0 | 4.6 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 245.8 | 0.0 | 236.0 | 232.1 | 232.1 | 0.0 | 0.0 | 3.9 | [5.2, 4.6] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw8 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 241.2 | 0.0 | 236.0 | 232.1 | 232.1 | 0.0 | 0.0 | 3.9 | [5.2, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 261.5 | 0.0 | 236.0 | 232.1 | 0.0 | 232.1 | 0.0 | 3.9 | [5.2, 4.6, 4.6, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 241.2 | 0.0 | 236.0 | 232.1 | 232.1 | 0.0 | 0.0 | 3.9 | [5.2] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw10 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 236.1 | 0.0 | 236.0 | 232.1 | 232.1 | 0.0 | 0.0 | 3.9 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw11 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 241.2 | 0.0 | 236.0 | 232.0 | 0.0 | 232.0 | 0.0 | 4.0 | [5.2] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw12 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 241.0 | 0.0 | 235.8 | 232.0 | 0.0 | 232.0 | 0.0 | 3.9 | [5.2] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw7 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 243.2 | 0.0 | 236.0 | 232.1 | 232.1 | 0.0 | 0.0 | 3.9 | [4.9] | 0.0 | 2.3 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw13 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 238.8 | 0.0 | 236.0 | 232.1 | 232.1 | 0.0 | 0.0 | 3.9 | [] | 0.0 | 2.9 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw38 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 180.4 | 0.0 | 174.9 | 172.3 | 0.0 | 172.3 | 0.0 | 2.6 | [0.0, 0.0, 0.0] | 0.0 | 5.4 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw5 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 261.5}, {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 20.0}] |
| second | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 20.0} |
| initial_second_predicted | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "nodes": 1, "nodeids": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"]} |
| initial_second_observed_matches | True |
| third_or_later | False |
| collection_matches | {"gw4": null, "gw3": null, "gw1": null, "gw9": null, "gw14": null, "gw5": null, "gw10": null, "gw6": null, "gw0": null, "gw7": null, "gw2": null, "gw11": null, "gw12": null, "gw13": null, "gw15": null, "gw8": null, "gw20": null, "gw16": null, "gw22": null, "gw31": null, "gw21": null, "gw24": null, "gw17": null, "gw34": null, "gw25": null, "gw19": null, "gw26": null, "gw27": null, "gw23": null, "gw28": null, "gw33": null, "gw36": null, "gw18": null, "gw29": null, "gw32": null, "gw37": null, "gw42": null, "gw30": null, "gw41": null, "gw35": null, "gw43": null, "gw46": null, "gw40": null, "gw38": null, "gw39": null, "gw44": null, "gw47": null, "gw45": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 120.9 |
| execution_interval | 281.5 |
| last_test_to_sessionfinish | 8.7 |
| outer_minus_junit | 1.3 |
| execution_minus_occupancy | 0.0 |
| (省略: 4830 bytes の行。原本は job dir analysis/cold/analysis.md) |
| (省略: 84057 bytes の行。原本は job dir analysis/cold/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw10": 0.0, "gw11": 0.0, "gw12": 0.0, "gw13": 0.0, "gw38": 0.0, "gw4": 0.0, "gw5": 0.0, "gw6": 0.0, "gw7": 0.0, "gw8": 0.0, "gw9": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

model

| metric | value |
|---|---|
| A_model | 390.8 |
| A_residual | 20.0 |
| assumptions | Fixed durations and F_A; lower-bound model, not implementation effect. Independent split loses same-root positive-to-mutation continuity; duplicated observed helper/setup/teardown. Build executed once in reality; both waits may recur. Session cleanup change is unmodeled. |
| L_reduce | 261.5 |
| D_reduce | 7962.8 |
| reduce_model | 390.8 |
| reduce_gain_model | 0.0 |
| d_positive | 245.8 |
| d_defect | 251.7 |
| positive_other | 0.0 |
| mutation_plus_defect_other | 2.1 |
| call_boundary_other | 0.0 |
| L_split | 254.7 |
| D_split | 8927.0 |
| split_model | 384.0 |
| split_gain_model | 6.8 |

## job4-01-C

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | 289.8 | 1789703139.5 |
| orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication | 20.0 | 1789703429.4 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw4 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 289.8 | 0.0 | 271.2 | 267.8 | 0.0 | 267.8 | 0.0 | 3.4 | [0.0, 4.9, 4.6, 4.5] | 0.0 | 4.5 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 280.9 | 0.0 | 271.3 | 267.9 | 267.9 | 0.0 | 0.0 | 3.4 | [5.1, 4.6] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw7 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 276.2 | 0.0 | 271.3 | 267.9 | 267.9 | 0.0 | 0.0 | 3.4 | [4.9, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw8 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 276.2 | 0.0 | 271.3 | 267.9 | 267.9 | 0.0 | 0.0 | 3.4 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 271.4 | 0.0 | 271.3 | 267.9 | 0.0 | 267.9 | 0.0 | 3.4 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw10 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 276.3 | 0.0 | 271.3 | 267.9 | 0.0 | 267.9 | 0.0 | 3.4 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw11 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 276.2 | 0.0 | 271.3 | 267.9 | 0.0 | 267.9 | 0.0 | 3.4 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 278.3 | 0.0 | 271.3 | 267.9 | 267.9 | 0.0 | 0.0 | 3.4 | [4.9] | 0.0 | 2.1 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw12 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 273.9 | 0.0 | 271.3 | 267.9 | 267.9 | 0.0 | 0.0 | 3.4 | [] | 0.0 | 2.7 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw37 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 216.2 | 0.0 | 210.8 | 208.3 | 0.0 | 208.3 | 0.0 | 2.5 | [0.0, 0.0, 0.0] | 0.0 | 5.4 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw4 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5"], "duration": 289.8}, {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 20.0}] |
| second | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 20.0} |
| initial_second_predicted | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "nodes": 1, "nodeids": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"]} |
| initial_second_observed_matches | True |
| third_or_later | False |
| collection_matches | {"gw3": null, "gw7": null, "gw0": null, "gw8": null, "gw15": null, "gw9": null, "gw6": null, "gw16": null, "gw2": null, "gw13": null, "gw1": null, "gw5": null, "gw18": null, "gw10": null, "gw12": null, "gw4": null, "gw19": null, "gw20": null, "gw11": null, "gw21": null, "gw17": null, "gw29": null, "gw14": null, "gw31": null, "gw27": null, "gw30": null, "gw26": null, "gw34": null, "gw28": null, "gw32": null, "gw25": null, "gw23": null, "gw22": null, "gw35": null, "gw33": null, "gw37": null, "gw40": null, "gw36": null, "gw24": null, "gw45": null, "gw47": null, "gw39": null, "gw42": null, "gw38": null, "gw43": null, "gw44": null, "gw41": null, "gw46": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 120.8 |
| execution_interval | 309.9 |
| last_test_to_sessionfinish | 8.6 |
| outer_minus_junit | 1.3 |
| execution_minus_occupancy | 0.0 |
| (省略: 4392 bytes の行。原本は job dir analysis/cold/analysis.md) |
| (省略: 84056 bytes の行。原本は job dir analysis/cold/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw10": 0.0, "gw11": 0.0, "gw12": 0.0, "gw37": 0.0, "gw4": 0.0, "gw5": 0.0, "gw6": 0.0, "gw7": 0.0, "gw8": 0.0, "gw9": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

## job4-02-A

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 286.6 | 1789703583.8 |
| orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication | 19.9 | 1789703870.5 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw4 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 280.3 | 0.0 | 261.4 | 257.4 | 0.0 | 257.4 | 0.0 | 4.0 | [0.0, 5.2, 4.6, 4.5] | 0.0 | 4.6 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 271.0 | 0.0 | 261.1 | 257.2 | 257.2 | 0.0 | 0.0 | 3.9 | [5.3, 4.6] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw8 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 266.4 | 0.0 | 261.1 | 257.2 | 257.2 | 0.0 | 0.0 | 3.9 | [5.3, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 286.6 | 0.0 | 261.1 | 257.2 | 257.2 | 0.0 | 0.0 | 3.9 | [5.3, 4.6, 4.5, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 266.4 | 0.0 | 261.1 | 257.2 | 257.2 | 0.0 | 0.0 | 3.9 | [5.3] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw10 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 261.2 | 0.0 | 261.1 | 257.2 | 257.2 | 0.0 | 0.0 | 3.9 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw11 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 266.4 | 0.0 | 261.2 | 257.3 | 0.0 | 257.3 | 0.0 | 3.9 | [5.3] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw12 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 266.7 | 0.0 | 261.4 | 257.5 | 0.0 | 257.5 | 0.0 | 3.9 | [5.2] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw7 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 268.5 | 0.0 | 261.1 | 257.2 | 0.0 | 257.2 | 0.0 | 3.9 | [4.9] | 0.0 | 2.4 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw13 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 264.1 | 0.0 | 261.1 | 257.2 | 257.2 | 0.0 | 0.0 | 3.9 | [] | 0.0 | 3.0 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw38 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 205.6 | 0.0 | 200.1 | 197.5 | 0.0 | 197.5 | 0.0 | 2.6 | [0.0, 0.0, 0.0] | 0.0 | 5.5 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw5 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 286.6}, {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 19.9}] |
| second | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 19.9} |
| initial_second_predicted | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "nodes": 1, "nodeids": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"]} |
| initial_second_observed_matches | True |
| third_or_later | False |
| collection_matches | {"gw1": null, "gw6": null, "gw2": null, "gw8": null, "gw0": null, "gw5": null, "gw14": null, "gw4": null, "gw18": null, "gw3": null, "gw16": null, "gw11": null, "gw10": null, "gw7": null, "gw17": null, "gw9": null, "gw19": null, "gw24": null, "gw12": null, "gw25": null, "gw20": null, "gw13": null, "gw22": null, "gw15": null, "gw26": null, "gw23": null, "gw32": null, "gw21": null, "gw28": null, "gw27": null, "gw29": null, "gw38": null, "gw35": null, "gw34": null, "gw46": null, "gw37": null, "gw33": null, "gw31": null, "gw39": null, "gw40": null, "gw44": null, "gw47": null, "gw36": null, "gw41": null, "gw45": null, "gw43": null, "gw30": null, "gw42": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 120.3 |
| execution_interval | 306.6 |
| last_test_to_sessionfinish | 8.6 |
| outer_minus_junit | 1.3 |
| execution_minus_occupancy | 0.0 |
| (省略: 4830 bytes の行。原本は job dir analysis/cold/analysis.md) |
| (省略: 84057 bytes の行。原本は job dir analysis/cold/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw10": 0.0, "gw11": 0.0, "gw12": 0.0, "gw13": 0.0, "gw38": 0.0, "gw4": 0.0, "gw5": 0.0, "gw6": 0.0, "gw7": 0.0, "gw8": 0.0, "gw9": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

model

| metric | value |
|---|---|
| A_model | 415.3 |
| A_residual | 19.9 |
| assumptions | Fixed durations and F_A; lower-bound model, not implementation effect. Independent split loses same-root positive-to-mutation continuity; duplicated observed helper/setup/teardown. Build executed once in reality; both waits may recur. Session cleanup change is unmodeled. |
| L_reduce | 286.6 |
| D_reduce | 8926.6 |
| reduce_model | 415.3 |
| reduce_gain_model | 0.0 |
| d_positive | 271.0 |
| d_defect | 276.7 |
| positive_other | 0.0 |
| mutation_plus_defect_other | 2.1 |
| call_boundary_other | 0.0 |
| L_split | 280.3 |
| D_split | 9991.6 |
| split_model | 409.1 |
| split_gain_model | 6.3 |

## job4-03-B

除外 (rc != 0; controller exitstatus != 0; FileNotFoundError(2, 'No such file or directory'))

## job5-01-B

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 216.4 | 1789705297.6 |
| orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases | 0.0 | 1789705514.1 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw4 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 210.2 | 0.0 | 191.5 | 187.5 | 0.0 | 187.5 | 0.0 | 3.9 | [0.0, 5.1, 4.6, 4.5] | 0.0 | 4.6 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 200.7 | 0.0 | 190.9 | 186.9 | 186.9 | 0.0 | 0.0 | 4.0 | [5.2, 4.6] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw8 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 196.2 | 0.0 | 190.9 | 186.9 | 186.9 | 0.0 | 0.0 | 4.0 | [5.2, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 216.4 | 0.0 | 190.9 | 186.9 | 186.9 | 0.0 | 0.0 | 4.0 | [5.2, 4.6, 4.6, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 196.1 | 0.0 | 190.9 | 186.9 | 186.9 | 0.0 | 0.0 | 4.0 | [5.2] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw10 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 191.0 | 0.0 | 190.9 | 186.9 | 186.9 | 0.0 | 0.0 | 4.0 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw11 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 196.3 | 0.0 | 191.2 | 187.1 | 0.0 | 187.1 | 0.0 | 4.0 | [5.2] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw12 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 196.1 | 0.0 | 191.0 | 186.9 | 0.0 | 186.9 | 0.0 | 4.0 | [5.2] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw7 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 198.1 | 0.0 | 190.9 | 186.9 | 186.9 | 0.0 | 0.0 | 4.0 | [4.9] | 0.0 | 2.3 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw13 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 193.8 | 0.0 | 190.9 | 186.9 | 0.0 | 186.9 | 0.0 | 4.0 | [] | 0.0 | 2.9 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw38 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 135.1 | 0.0 | 129.6 | 127.0 | 0.0 | 127.0 | 0.0 | 2.6 | [0.0, 0.0, 0.0] | 0.0 | 5.4 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw5 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 216.4}, {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases", "cost": 0.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases"], "duration": 0.0}] |
| second | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases", "cost": 0.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases"], "duration": 0.0} |
| initial_second_predicted | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases", "cost": 0.0, "nodes": 1, "nodeids": ["orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases"]} |
| initial_second_observed_matches | True |
| third_or_later | False |
| collection_matches | {"gw2": true, "gw7": true, "gw0": true, "gw4": true, "gw15": true, "gw1": true, "gw5": true, "gw10": true, "gw11": true, "gw8": true, "gw9": true, "gw3": true, "gw21": true, "gw13": true, "gw6": true, "gw12": true, "gw14": true, "gw16": true, "gw22": true, "gw19": true, "gw18": true, "gw17": true, "gw25": true, "gw20": true, "gw26": true, "gw23": true, "gw31": true, "gw24": true, "gw35": true, "gw28": true, "gw27": true, "gw33": true, "gw37": true, "gw39": true, "gw30": true, "gw32": true, "gw38": true, "gw36": true, "gw34": true, "gw40": true, "gw41": true, "gw42": true, "gw44": true, "gw47": true, "gw46": true, "gw43": true, "gw29": true, "gw45": true} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 119.7 |
| execution_interval | 216.4 |
| last_test_to_sessionfinish | 8.6 |
| outer_minus_junit | 1.3 |
| execution_minus_occupancy | 0.0 |
| (省略: 4852 bytes の行。原本は job dir analysis/cold/analysis.md) |
| (省略: 84345 bytes の行。原本は job dir analysis/cold/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw10": 0.0, "gw11": 0.0, "gw12": 0.0, "gw13": 0.0, "gw38": 0.0, "gw4": 0.0, "gw5": 0.0, "gw6": 0.0, "gw7": 0.0, "gw8": 0.0, "gw9": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

## 条件別中央値と全走の値

S1

| metric | values | median | n |
|---|---|---|---|
| W | [] | — | 0 |
| O | [] | — | 0 |
| F | [] | — | 0 |
| L | [] | — | 0 |
| P | [] | — | 0 |
| D | [] | — | 0 |
| mean_load | [] | — | 0 |
| outer_wall | [] | — | 0 |

M 成分の中央値と全値（各 node/指標を個別集計）

| nodeid | metric | values | median | n |
|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call_other | [] | — | 0 |

| metric | values | median | n |
|---|---|---|---|

| metric | values | median | n |
|---|---|---|---|
| session_to_first_test | [] | — | 0 |
| execution_interval | [] | — | 0 |
| last_test_to_sessionfinish | [] | — | 0 |
| outer_minus_junit | [] | — | 0 |
| execution_minus_occupancy | [] | — | 0 |

S

| metric | values | median | n |
|---|---|---|---|
| W | [] | — | 0 |
| O | [] | — | 0 |
| F | [] | — | 0 |
| L | [] | — | 0 |
| P | [] | — | 0 |
| D | [] | — | 0 |
| mean_load | [] | — | 0 |
| outer_wall | [] | — | 0 |

M 成分の中央値と全値（各 node/指標を個別集計）

| nodeid | metric | values | median | n |
|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call_other | [] | — | 0 |

| metric | values | median | n |
|---|---|---|---|

| metric | values | median | n |
|---|---|---|---|
| session_to_first_test | [] | — | 0 |
| execution_interval | [] | — | 0 |
| last_test_to_sessionfinish | [] | — | 0 |
| outer_minus_junit | [] | — | 0 |
| execution_minus_occupancy | [] | — | 0 |

A

| metric | values | median | n |
|---|---|---|---|
| W | [414.7, 410.7, 435.3] | 414.7 | 3 |
| O | [285.2, 281.4, 306.5] | 285.2 | 3 |
| F | [129.4, 129.3, 128.7] | 129.3 | 3 |
| L | [265.3, 261.5, 286.6] | 265.3 | 3 |
| P | [19.9, 20.0, 19.9] | 19.9 | 3 |
| D | [8904.5, 8691.0, 9730.5] | 8904.5 | 3 |
| mean_load | [185.5, 181.1, 202.7] | 185.5 | 3 |
| outer_wall | [415.9, 412.0, 436.6] | 415.9 | 3 |

M 成分の中央値と全値（各 node/指標を個別集計）

| nodeid | metric | values | median | n |
|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call | [258.5, 254.7, 280.3] | 258.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper | [239.6, 235.7, 261.4] | 239.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get | [235.7, 231.9, 257.4] | 235.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | build | [235.7, 231.9, 257.4] | 235.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | copytree_top | [3.9, 3.8, 4.0] | 3.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call_other | [4.6, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_1 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_2 | [5.2, 5.2, 5.2] | 5.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_3 | [4.6, 4.7, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_4 | [4.5, 4.5, 4.5] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call | [249.2, 245.8, 271.0] | 249.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper | [239.4, 236.0, 261.1] | 239.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get | [235.5, 232.1, 257.2] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | flock_ex | [235.5, 232.1, 257.2] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | copytree_top | [3.8, 3.9, 3.9] | 3.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | verify_1 | [5.3, 5.2, 5.3] | 5.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | verify_2 | [4.6, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call | [244.7, 241.2, 266.4] | 244.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper | [239.3, 236.0, 261.1] | 239.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get | [235.5, 232.1, 257.2] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | flock_ex | [235.5, 232.1, 257.2] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | copytree_top | [3.8, 3.9, 3.9] | 3.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | verify_1 | [5.3, 5.2, 5.3] | 5.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | verify_2 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call | [265.3, 261.5, 286.6] | 265.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper | [239.4, 236.0, 261.1] | 239.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get | [235.5, 232.1, 257.2] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | flock_ex | [0.0, 0.0, 257.2] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | build | [235.5, 232.1, 0.0] | 232.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | copytree_top | [3.8, 3.9, 3.9] | 3.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call_other | [2.1, 2.1, 2.1] | 2.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_1 | [5.3, 5.2, 5.3] | 5.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_2 | [4.8, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_3 | [4.7, 4.6, 4.5] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_4 | [4.5, 4.5, 4.5] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_5 | [4.5, 4.5, 4.5] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call | [244.6, 241.2, 266.4] | 244.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper | [239.4, 236.0, 261.1] | 239.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get | [235.5, 232.1, 257.2] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | flock_ex | [235.5, 232.1, 257.2] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | copytree_top | [3.8, 3.9, 3.9] | 3.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | verify_1 | [5.3, 5.2, 5.3] | 5.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call | [239.5, 236.1, 261.2] | 239.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper | [239.4, 236.0, 261.1] | 239.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get | [235.5, 232.1, 257.2] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | flock_ex | [235.5, 232.1, 257.2] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | copytree_top | [3.8, 3.9, 3.9] | 3.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call_other | [0.1, 0.1, 0.1] | 0.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call | [244.7, 241.2, 266.4] | 244.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper | [239.4, 236.0, 261.2] | 239.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get | [235.5, 232.0, 257.3] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | build | [235.5, 232.0, 257.3] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | copytree_top | [3.9, 4.0, 3.9] | 3.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | verify_1 | [5.3, 5.2, 5.3] | 5.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call | [244.8, 241.0, 266.7] | 244.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper | [239.7, 235.8, 261.4] | 239.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get | [235.8, 232.0, 257.5] | 235.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | build | [235.8, 232.0, 257.5] | 235.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | copytree_top | [3.9, 3.9, 3.9] | 3.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | verify_1 | [5.2, 5.2, 5.2] | 5.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call | [246.7, 243.2, 268.5] | 246.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper | [239.4, 236.0, 261.1] | 239.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get | [235.5, 232.1, 257.2] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | flock_ex | [235.5, 232.1, 0.0] | 232.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | build | [0.0, 0.0, 257.2] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | copytree_top | [3.8, 3.9, 3.9] | 3.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call_other | [2.4, 2.3, 2.4] | 2.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | verify_1 | [5.0, 4.9, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call | [242.3, 238.8, 264.1] | 242.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper | [239.4, 236.0, 261.1] | 239.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get | [235.5, 232.1, 257.2] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | flock_ex | [235.5, 232.1, 257.2] | 235.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | copytree_top | [3.8, 3.9, 3.9] | 3.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call_other | [2.9, 2.9, 3.0] | 2.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call | [184.1, 180.4, 205.6] | 184.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper | [178.6, 174.9, 200.1] | 178.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get | [176.0, 172.3, 197.5] | 176.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | build | [176.0, 172.3, 197.5] | 176.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | copytree_top | [2.6, 2.6, 2.6] | 2.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call_other | [5.4, 5.4, 5.5] | 5.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_1 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_2 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_3 | [0.0, 0.0, 0.0] | 0.0 | 3 |

| metric | values | median | n |
|---|---|---|---|
| A_model | [394.7, 390.8, 415.3] | 394.7 | 3 |
| A_residual | [19.9, 20.0, 19.9] | 19.9 | 3 |
| D_reduce | [8165.9, 7962.8, 8926.6] | 8165.9 | 3 |
| D_split | [9143.8, 8927.0, 9991.6] | 9143.8 | 3 |
| L_reduce | [265.3, 261.5, 286.6] | 265.3 | 3 |
| L_split | [258.5, 254.7, 280.3] | 258.5 | 3 |
| call_boundary_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| d_defect | [255.2, 251.7, 276.7] | 255.2 | 3 |
| d_positive | [249.5, 245.8, 271.0] | 249.5 | 3 |
| mutation_plus_defect_other | [2.1, 2.1, 2.1] | 2.1 | 3 |
| positive_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| reduce_gain_model | [-0.0, 0.0, 0.0] | 0.0 | 3 |
| reduce_model | [394.7, 390.8, 415.3] | 394.7 | 3 |
| split_gain_model | [6.8, 6.8, 6.3] | 6.8 | 3 |
| split_model | [387.9, 384.0, 409.1] | 387.9 | 3 |

| metric | values | median | n |
|---|---|---|---|
| session_to_first_test | [120.9, 120.9, 120.3] | 120.9 | 3 |
| execution_interval | [285.3, 281.5, 306.6] | 285.3 | 3 |
| last_test_to_sessionfinish | [8.7, 8.7, 8.6] | 8.7 | 3 |
| outer_minus_junit | [1.2, 1.3, 1.3] | 1.3 | 3 |
| execution_minus_occupancy | [0.0, 0.0, 0.0] | 0.0 | 3 |

B

| metric | values | median | n |
|---|---|---|---|
| W | [362.6, 345.6, 344.4] | 345.6 | 3 |
| O | [232.1, 217.1, 216.4] | 217.1 | 3 |
| F | [130.5, 128.5, 128.0] | 128.5 | 3 |
| L | [232.1, 217.1, 216.4] | 217.1 | 3 |
| P | [0.0, -0.0, 0.0] | 0.0 | 3 |
| D | [7740.5, 7433.9, 7559.2] | 7559.2 | 3 |
| mean_load | [161.3, 154.9, 157.5] | 157.5 | 3 |
| outer_wall | [363.9, 346.9, 345.7] | 346.9 | 3 |

M 成分の中央値と全値（各 node/指標を個別集計）

| nodeid | metric | values | median | n |
|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call | [225.5, 210.6, 210.2] | 210.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper | [206.5, 191.8, 191.5] | 191.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get | [202.2, 187.7, 187.5] | 187.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | build | [202.2, 187.7, 187.5] | 187.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | copytree_top | [4.3, 4.1, 3.9] | 4.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call_other | [4.6, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_1 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_2 | [5.3, 5.1, 5.1] | 5.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_3 | [4.6, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_4 | [4.5, 4.5, 4.5] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call | [216.4, 201.5, 200.7] | 201.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper | [206.5, 191.8, 190.9] | 191.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get | [202.2, 187.8, 186.9] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | flock_ex | [202.2, 187.8, 186.9] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | copytree_top | [4.3, 4.0, 4.0] | 4.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | verify_1 | [5.3, 5.1, 5.2] | 5.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | verify_2 | [4.6, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call | [211.8, 196.9, 196.2] | 196.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper | [206.5, 191.8, 190.9] | 191.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get | [202.2, 187.8, 186.9] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | flock_ex | [202.2, 187.8, 186.9] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | copytree_top | [4.3, 4.0, 4.0] | 4.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | verify_1 | [5.3, 5.1, 5.2] | 5.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | verify_2 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call | [232.1, 217.1, 216.4] | 217.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper | [206.5, 191.7, 190.9] | 191.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get | [202.2, 187.8, 186.9] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | flock_ex | [202.2, 187.8, 186.9] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | copytree_top | [4.3, 3.9, 4.0] | 4.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call_other | [2.1, 2.1, 2.1] | 2.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_1 | [5.3, 5.1, 5.2] | 5.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_2 | [4.6, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_3 | [4.5, 4.5, 4.6] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_4 | [4.5, 4.5, 4.5] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_5 | [4.5, 4.5, 4.5] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call | [211.8, 196.9, 196.1] | 196.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper | [206.5, 191.8, 190.9] | 191.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get | [202.2, 187.8, 186.9] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | flock_ex | [202.2, 187.8, 186.9] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | copytree_top | [4.3, 4.0, 4.0] | 4.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | verify_1 | [5.3, 5.2, 5.2] | 5.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call | [206.6, 191.9, 191.0] | 191.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper | [206.5, 191.8, 190.9] | 191.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get | [202.2, 187.8, 186.9] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | flock_ex | [202.2, 187.8, 186.9] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | copytree_top | [4.3, 4.0, 4.0] | 4.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call_other | [0.1, 0.1, 0.1] | 0.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call | [211.9, 196.9, 196.3] | 196.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper | [206.6, 191.8, 191.2] | 191.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get | [202.3, 187.7, 187.1] | 187.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | build | [202.3, 187.7, 187.1] | 187.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | copytree_top | [4.3, 4.1, 4.0] | 4.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | verify_1 | [5.3, 5.1, 5.2] | 5.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call | [211.9, 196.8, 196.1] | 196.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper | [206.7, 191.7, 191.0] | 191.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get | [202.3, 187.6, 186.9] | 187.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | build | [202.3, 187.6, 186.9] | 187.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | copytree_top | [4.3, 4.0, 4.0] | 4.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | verify_1 | [5.2, 5.1, 5.2] | 5.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call | [213.9, 199.0, 198.1] | 199.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper | [206.5, 191.8, 190.9] | 191.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get | [202.2, 187.8, 186.9] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | flock_ex | [0.0, 0.0, 186.9] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | build | [202.2, 187.8, 0.0] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | copytree_top | [4.3, 4.0, 4.0] | 4.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call_other | [2.5, 2.3, 2.3] | 2.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | verify_1 | [4.9, 4.9, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call | [209.5, 194.7, 193.8] | 194.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper | [206.5, 191.9, 190.9] | 191.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get | [202.2, 187.8, 186.9] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | flock_ex | [202.2, 187.8, 0.0] | 187.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | build | [0.0, 0.0, 186.9] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | copytree_top | [4.3, 4.1, 4.0] | 4.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call_other | [3.0, 2.8, 2.9] | 2.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call | [150.6, 135.9, 135.1] | 135.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper | [144.9, 130.4, 129.6] | 130.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get | [142.3, 127.8, 127.0] | 127.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | build | [142.3, 127.8, 127.0] | 127.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | copytree_top | [2.6, 2.6, 2.6] | 2.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call_other | [5.6, 5.5, 5.4] | 5.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_1 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_2 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_3 | [0.0, 0.0, 0.0] | 0.0 | 3 |

| metric | values | median | n |
|---|---|---|---|

| metric | values | median | n |
|---|---|---|---|
| session_to_first_test | [120.2, 120.2, 119.7] | 120.2 | 3 |
| execution_interval | [234.1, 217.1, 216.4] | 217.1 | 3 |
| last_test_to_sessionfinish | [8.6, 8.5, 8.6] | 8.6 | 3 |
| outer_minus_junit | [1.3, 1.3, 1.3] | 1.3 | 3 |
| execution_minus_occupancy | [2.0, 0.0, 0.0] | 0.0 | 3 |

C

| metric | values | median | n |
|---|---|---|---|
| W | [412.0, 417.8, 438.9] | 417.8 | 3 |
| O | [283.8, 288.8, 309.8] | 288.8 | 3 |
| F | [128.2, 129.0, 129.1] | 129.0 | 3 |
| L | [263.4, 268.8, 289.8] | 268.8 | 3 |
| P | [20.4, 20.0, 20.0] | 20.0 | 3 |
| D | [8909.2, 9226.5, 10005.6] | 9226.5 | 3 |
| mean_load | [185.6, 192.2, 208.4] | 192.2 | 3 |
| outer_wall | [413.3, 419.1, 440.3] | 419.1 | 3 |

M 成分の中央値と全値（各 node/指標を個別集計）

| nodeid | metric | values | median | n |
|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call | [263.4, 268.8, 289.8] | 268.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper | [244.8, 250.2, 271.2] | 250.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get | [241.3, 246.6, 267.8] | 246.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | build | [241.3, 246.6, 267.8] | 246.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | copytree_top | [3.5, 3.6, 3.4] | 3.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call_other | [4.6, 4.6, 4.5] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_1 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_2 | [4.9, 4.9, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_3 | [4.6, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_4 | [4.5, 4.5, 4.5] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call | [254.8, 259.7, 280.9] | 259.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper | [245.0, 250.2, 271.3] | 250.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get | [241.5, 246.6, 267.9] | 246.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | flock_ex | [241.5, 246.6, 267.9] | 246.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | copytree_top | [3.5, 3.5, 3.4] | 3.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | verify_1 | [5.1, 4.9, 5.1] | 5.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | verify_2 | [4.7, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call | [250.0, 255.1, 276.2] | 255.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper | [245.0, 250.2, 271.3] | 250.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get | [241.5, 246.6, 267.9] | 246.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | flock_ex | [241.5, 246.6, 267.9] | 246.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | copytree_top | [3.5, 3.5, 3.4] | 3.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | verify_1 | [5.0, 5.0, 4.9] | 5.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | verify_2 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | setup | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | teardown | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | flock_ex | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | build | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | copytree_top | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call_other | [] | — | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call | [250.0, 255.1, 276.2] | 255.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper | [245.0, 250.2, 271.3] | 250.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get | [241.5, 246.6, 267.9] | 246.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | flock_ex | [241.5, 246.6, 267.9] | 246.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | copytree_top | [3.5, 3.5, 3.4] | 3.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | verify_1 | [5.0, 5.0, 4.9] | 5.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call | [245.1, 250.2, 271.4] | 250.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper | [245.0, 250.2, 271.3] | 250.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get | [241.5, 246.6, 267.9] | 246.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | flock_ex | [0.0, 246.6, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | build | [241.5, 0.0, 267.9] | 241.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | copytree_top | [3.5, 3.5, 3.4] | 3.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call_other | [0.1, 0.1, 0.1] | 0.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call | [249.8, 255.3, 276.3] | 255.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper | [244.8, 250.4, 271.3] | 250.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get | [241.3, 246.9, 267.9] | 246.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | build | [241.3, 246.9, 267.9] | 246.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | copytree_top | [3.5, 3.5, 3.4] | 3.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | verify_1 | [5.0, 4.9, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call | [249.8, 255.3, 276.2] | 255.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper | [244.9, 250.3, 271.3] | 250.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get | [241.4, 246.8, 267.9] | 246.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | build | [241.4, 246.8, 267.9] | 246.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | copytree_top | [3.5, 3.5, 3.4] | 3.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | verify_1 | [4.9, 4.9, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call | [252.1, 257.2, 278.3] | 257.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper | [245.0, 250.2, 271.3] | 250.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get | [241.5, 246.6, 267.9] | 246.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | flock_ex | [241.5, 246.6, 267.9] | 246.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | copytree_top | [3.5, 3.5, 3.4] | 3.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call_other | [2.1, 2.1, 2.1] | 2.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | verify_1 | [5.0, 4.9, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call | [247.7, 252.9, 273.9] | 252.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper | [245.0, 250.2, 271.3] | 250.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get | [241.5, 246.6, 267.9] | 246.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | flock_ex | [241.5, 0.0, 267.9] | 241.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | build | [0.0, 246.6, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | copytree_top | [3.5, 3.5, 3.4] | 3.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call_other | [2.7, 2.7, 2.7] | 2.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call | [189.6, 195.4, 216.2] | 195.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper | [184.2, 189.5, 210.8] | 189.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get | [181.6, 186.9, 208.3] | 186.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | build | [181.6, 186.9, 208.3] | 186.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | copytree_top | [2.6, 2.6, 2.5] | 2.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call_other | [5.4, 5.8, 5.4] | 5.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_1 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_2 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_3 | [0.0, 0.0, 0.0] | 0.0 | 3 |

| metric | values | median | n |
|---|---|---|---|

| metric | values | median | n |
|---|---|---|---|
| session_to_first_test | [119.7, 120.6, 120.8] | 120.6 | 3 |
| execution_interval | [283.8, 288.8, 309.9] | 288.8 | 3 |
| last_test_to_sessionfinish | [8.7, 8.7, 8.6] | 8.7 | 3 |
| outer_minus_junit | [1.3, 1.2, 1.3] | 1.3 | 3 |
| execution_minus_occupancy | [0.0, 0.0, 0.0] | 0.0 | 3 |

## job 内の対差

A−B

| metric | value |
|---|---|
| (省略: 1968 bytes の行。原本は job dir analysis/cold/analysis.md) |
| values | [52.0, 65.1] |
| median | 58.6 |
| n | 2 |
| difference_of_medians | 69.0 |
| interpretation | 採用効果は未確立 |
| scope | replica; C is diagnostic, not an upper bound; single-run 10% rule is not a median rule |

A−C

| metric | value |
|---|---|
| (省略: 2556 bytes の行。原本は job dir analysis/cold/analysis.md) |
| values | [2.7, -7.1, -3.7] |
| median | -3.7 |
| n | 3 |
| difference_of_medians | -3.2 |
| interpretation | 採用効果は未確立 |
| scope | replica; C is diagnostic, not an upper bound; single-run 10% rule is not a median rule |

## 歴史照合

| metric | value |
|---|---|
| I | False |
| n_history | 93 |
| n_A | 3 |
| metrics | {"W": {"inside": [true, true, true], "range": [310.8, 677.1], "percentiles": [0.8, 0.8, 0.8], "percentiles_percent": [76.3, 75.3, 76.3], "median_ratio": 1.1}, "O": {"inside": [true, true, true], "range": [243.8, 578.0], "percentiles": [0.3, 0.3, 0.6], "percentiles_percent": [33.3, 25.8, 61.3], "median_ratio": 1.0}, "F": {"inside": [false, false, false], "range": [65.0, 103.3], "percentiles": [1.0, 1.0, 1.0], "percentiles_percent": [100.0, 100.0, 100.0], "median_ratio": 1.9}, "L": {"inside": [true, true, true], "range": [200.0, 557.7], "percentiles": [0.3, 0.3, 0.6], "percentiles_percent": [32.3, 25.8, 61.3], "median_ratio": 1.0}} |
| note | Descriptive inclusion, not equivalence; history rounded to 0.1 seconds. |

## 総括

失敗・未完走・記録失敗は除外。3/3 の同符号は有意差ではない。分割は連続検査、縮約は 3 欠陥型の検出を失う案。実装効果・他 shard への利益は未測定。
