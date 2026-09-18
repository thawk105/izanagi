## 対象と定義

replica shard-0 の同一 tip 反復。受入証跡ではない。model は下限参考値。

走数 3、採用 2。中央値は各走を分解した後、指標別に計算。

W=JUnit testsuite、L=JUnit testcase 最大、O=phase 合算最大、F=W−O、P=O−L、D=全 phase 合算。

## shard 表

| condition | run | host | ordinal | W | O | O_production | O_difference | F | L | longest_node | P | longest_on_busy | D | mean_load | busy_worker | busy_count | terminal | outer_wall | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | job6-01-A | bnode014 | 1 | 346.9 | 280.5 | 280.5 | 0.0 | 66.4 | 260.6 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 19.9 | True | 8532.7 | 177.8 | gw5 | 2 | {"selected": 3938, "executed_selected": 3938, "finished": 3938, "failed": 0, "skipped": 53, "rc": 0} | 348.1 | 採用 |
| A | job6-02-A | bnode014 | 2 | 345.8 | 279.4 | 279.4 | 0.0 | 66.4 | 259.5 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 19.9 | True | 8419.4 | 175.4 | gw5 | 2 | {"selected": 3938, "executed_selected": 3938, "finished": 3938, "failed": 0, "skipped": 53, "rc": 0} | 347.0 | 採用 |
| A | job6-03-A | bnode014 | 3 | 373.1 | 306.7 | 306.7 | 0.0 | 66.5 | 286.5 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 20.2 | True | 9570.8 | 199.4 | gw5 | 2 | {"selected": 3938, "executed_selected": 3938, "finished": 3938, "failed": 4, "skipped": 53, "rc": 1} | 374.3 | 除外 (rc != 0; controller exitstatus != 0; production report rc != 0; failed phase) |

## job6-01-A

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 260.7 | 1789706356.2 |
| orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication | 19.9 | 1789706616.9 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw4 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 253.6 | 0.0 | 234.9 | 231.4 | 0.0 | 231.4 | 0.0 | 3.5 | [0.0, 5.0, 4.6, 4.5] | 0.0 | 4.6 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 245.1 | 0.0 | 235.4 | 231.7 | 231.7 | 0.0 | 0.0 | 3.7 | [5.1, 4.6] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw8 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 240.5 | 0.0 | 235.4 | 231.7 | 231.7 | 0.0 | 0.0 | 3.7 | [5.1, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 260.6 | 0.0 | 235.4 | 231.7 | 0.0 | 231.7 | 0.0 | 3.7 | [5.1, 4.6, 4.5, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 240.5 | 0.0 | 235.4 | 231.7 | 231.7 | 0.0 | 0.0 | 3.7 | [5.1] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw10 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 235.5 | 0.0 | 235.4 | 231.7 | 231.7 | 0.0 | 0.0 | 3.7 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw11 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 240.3 | 0.0 | 235.2 | 231.5 | 0.0 | 231.5 | 0.0 | 3.6 | [5.1] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw12 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 240.2 | 0.0 | 235.1 | 231.5 | 0.0 | 231.5 | 0.0 | 3.6 | [5.1] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw7 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 242.5 | 0.0 | 235.4 | 231.7 | 231.7 | 0.0 | 0.0 | 3.7 | [4.9] | 0.0 | 2.3 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw13 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 238.2 | 0.0 | 235.4 | 231.7 | 231.7 | 0.0 | 0.0 | 3.7 | [] | 0.0 | 2.8 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw38 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 179.9 | 0.0 | 174.4 | 171.9 | 0.0 | 171.9 | 0.0 | 2.6 | [0.0, 0.0, 0.0] | 0.0 | 5.4 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw5 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 260.7}, {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 19.9}] |
| second | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 19.9} |
| initial_second_predicted | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "nodes": 1, "nodeids": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"]} |
| initial_second_observed_matches | True |
| third_or_later | False |
| collection_matches | {"gw8": null, "gw1": null, "gw2": null, "gw3": null, "gw4": null, "gw7": null, "gw6": null, "gw5": null, "gw9": null, "gw10": null, "gw0": null, "gw12": null, "gw11": null, "gw16": null, "gw21": null, "gw14": null, "gw18": null, "gw20": null, "gw15": null, "gw19": null, "gw17": null, "gw13": null, "gw22": null, "gw24": null, "gw25": null, "gw23": null, "gw29": null, "gw28": null, "gw30": null, "gw27": null, "gw33": null, "gw32": null, "gw26": null, "gw34": null, "gw35": null, "gw39": null, "gw31": null, "gw40": null, "gw38": null, "gw37": null, "gw36": null, "gw42": null, "gw45": null, "gw41": null, "gw43": null, "gw44": null, "gw47": null, "gw46": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 58.4 |
| execution_interval | 280.5 |
| last_test_to_sessionfinish | 8.2 |
| outer_minus_junit | 1.2 |
| execution_minus_occupancy | 0.0 |
| (省略: 4830 bytes の行。原本は job dir analysis/warm/analysis.md) |
| (省略: 84057 bytes の行。原本は job dir analysis/warm/analysis.md) |
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
| A_model | 327.0 |
| A_residual | 19.9 |
| assumptions | Fixed durations and F_A; lower-bound model, not implementation effect. Independent split loses same-root positive-to-mutation continuity; duplicated observed helper/setup/teardown. Build executed once in reality; both waits may recur. Session cleanup change is unmodeled. |
| L_reduce | 260.7 |
| D_reduce | 7806.6 |
| reduce_model | 327.0 |
| reduce_gain_model | -0.0 |
| d_positive | 245.0 |
| d_defect | 251.0 |
| positive_other | 0.0 |
| mutation_plus_defect_other | 2.1 |
| call_boundary_other | 0.0 |
| L_split | 253.6 |
| D_split | 8768.0 |
| split_model | 320.0 |
| split_gain_model | 7.0 |

## job6-02-A

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 259.5 | 1789706708.3 |
| orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication | 19.9 | 1789706967.8 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw4 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 253.1 | 0.0 | 234.1 | 230.2 | 0.0 | 230.2 | 0.0 | 4.0 | [0.0, 5.2, 4.6, 4.5] | 0.0 | 4.6 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 243.9 | 0.0 | 234.0 | 230.1 | 230.1 | 0.0 | 0.0 | 3.9 | [5.3, 4.6] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw8 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 239.4 | 0.0 | 234.0 | 230.1 | 230.1 | 0.0 | 0.0 | 3.9 | [5.3, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 259.5 | 0.0 | 234.0 | 230.1 | 230.1 | 0.0 | 0.0 | 3.9 | [5.3, 4.6, 4.6, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 239.3 | 0.0 | 234.0 | 230.1 | 230.1 | 0.0 | 0.0 | 3.9 | [5.3] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw10 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 234.1 | 0.0 | 234.0 | 230.1 | 230.1 | 0.0 | 0.0 | 3.9 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw11 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 239.3 | 0.0 | 234.0 | 230.1 | 0.0 | 230.1 | 0.0 | 3.9 | [5.2] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw12 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 239.4 | 0.0 | 234.2 | 230.3 | 0.0 | 230.3 | 0.0 | 4.0 | [5.2] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw7 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 241.3 | 0.0 | 234.0 | 230.1 | 230.1 | 0.0 | 0.0 | 3.9 | [4.9] | 0.0 | 2.4 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw13 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 236.9 | 0.0 | 234.0 | 230.1 | 0.0 | 230.1 | 0.0 | 3.9 | [] | 0.0 | 2.9 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw38 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 178.5 | 0.0 | 173.0 | 170.4 | 0.0 | 170.4 | 0.0 | 2.6 | [0.0, 0.0, 0.0] | 0.0 | 5.4 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw5 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 259.5}, {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 19.9}] |
| second | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "items": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"], "duration": 19.9} |
| initial_second_predicted | {"scope": "orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication", "cost": 23.0, "nodes": 1, "nodeids": ["orchestrator/tests/test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication"]} |
| initial_second_observed_matches | True |
| third_or_later | False |
| collection_matches | {"gw0": null, "gw3": null, "gw1": null, "gw2": null, "gw4": null, "gw7": null, "gw6": null, "gw5": null, "gw11": null, "gw9": null, "gw8": null, "gw14": null, "gw10": null, "gw12": null, "gw16": null, "gw15": null, "gw17": null, "gw13": null, "gw19": null, "gw18": null, "gw20": null, "gw21": null, "gw23": null, "gw22": null, "gw25": null, "gw26": null, "gw27": null, "gw24": null, "gw29": null, "gw34": null, "gw28": null, "gw33": null, "gw31": null, "gw32": null, "gw35": null, "gw30": null, "gw39": null, "gw38": null, "gw36": null, "gw41": null, "gw44": null, "gw43": null, "gw40": null, "gw37": null, "gw45": null, "gw47": null, "gw42": null, "gw46": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 58.3 |
| execution_interval | 279.5 |
| last_test_to_sessionfinish | 8.3 |
| outer_minus_junit | 1.2 |
| execution_minus_occupancy | 0.0 |
| (省略: 4830 bytes の行。原本は job dir analysis/warm/analysis.md) |
| (省略: 84057 bytes の行。原本は job dir analysis/warm/analysis.md) |
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
| A_model | 325.9 |
| A_residual | 19.9 |
| assumptions | Fixed durations and F_A; lower-bound model, not implementation effect. Independent split loses same-root positive-to-mutation continuity; duplicated observed helper/setup/teardown. Build executed once in reality; both waits may recur. Session cleanup change is unmodeled. |
| L_reduce | 259.5 |
| D_reduce | 7696.8 |
| reduce_model | 325.9 |
| reduce_gain_model | 0.0 |
| d_positive | 243.9 |
| d_defect | 249.7 |
| positive_other | 0.0 |
| mutation_plus_defect_other | 2.1 |
| call_boundary_other | 0.0 |
| L_split | 253.1 |
| D_split | 8653.4 |
| split_model | 319.5 |
| split_gain_model | 6.5 |

## job6-03-A

除外 (rc != 0; controller exitstatus != 0; production report rc != 0; failed phase)

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
| W | [346.9, 345.8] | 346.3 | 2 |
| O | [280.5, 279.4] | 280.0 | 2 |
| F | [66.4, 66.4] | 66.4 | 2 |
| L | [260.6, 259.5] | 260.1 | 2 |
| P | [19.9, 19.9] | 19.9 | 2 |
| D | [8532.7, 8419.4] | 8476.0 | 2 |
| mean_load | [177.8, 175.4] | 176.6 | 2 |
| outer_wall | [348.1, 347.0] | 347.5 | 2 |

M 成分の中央値と全値（各 node/指標を個別集計）

| nodeid | metric | values | median | n |
|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | setup | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call | [253.6, 253.1] | 253.4 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | teardown | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper | [234.9, 234.1] | 234.5 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get | [231.4, 230.2] | 230.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | flock_ex | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | build | [231.4, 230.2] | 230.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | copytree_top | [3.5, 4.0] | 3.7 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call_other | [4.6, 4.6] | 4.6 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_1 | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_2 | [5.0, 5.2] | 5.1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_3 | [4.6, 4.6] | 4.6 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_4 | [4.5, 4.5] | 4.5 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | setup | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call | [245.1, 243.9] | 244.5 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | teardown | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper | [235.4, 234.0] | 234.7 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get | [231.7, 230.1] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | flock_ex | [231.7, 230.1] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | build | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | copytree_top | [3.7, 3.9] | 3.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | verify_1 | [5.1, 5.3] | 5.2 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | verify_2 | [4.6, 4.6] | 4.6 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | setup | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call | [240.5, 239.4] | 239.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | teardown | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper | [235.4, 234.0] | 234.7 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get | [231.7, 230.1] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | flock_ex | [231.7, 230.1] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | build | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | copytree_top | [3.7, 3.9] | 3.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | verify_1 | [5.1, 5.3] | 5.2 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | verify_2 | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | setup | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call | [260.6, 259.5] | 260.1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | teardown | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper | [235.4, 234.0] | 234.7 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get | [231.7, 230.1] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | flock_ex | [0.0, 230.1] | 115.1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | build | [231.7, 0.0] | 115.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | copytree_top | [3.7, 3.9] | 3.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call_other | [2.1, 2.1] | 2.1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_1 | [5.1, 5.3] | 5.2 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_2 | [4.6, 4.6] | 4.6 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_3 | [4.5, 4.6] | 4.5 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_4 | [4.5, 4.5] | 4.5 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_5 | [4.5, 4.5] | 4.5 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | setup | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call | [240.5, 239.3] | 239.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | teardown | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper | [235.4, 234.0] | 234.7 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get | [231.7, 230.1] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | flock_ex | [231.7, 230.1] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | build | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | copytree_top | [3.7, 3.9] | 3.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | verify_1 | [5.1, 5.3] | 5.2 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | setup | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call | [235.5, 234.1] | 234.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | teardown | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper | [235.4, 234.0] | 234.7 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get | [231.7, 230.1] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | flock_ex | [231.7, 230.1] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | build | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | copytree_top | [3.7, 3.9] | 3.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call_other | [0.1, 0.1] | 0.1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | setup | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call | [240.3, 239.3] | 239.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | teardown | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper | [235.2, 234.0] | 234.6 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get | [231.5, 230.1] | 230.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | flock_ex | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | build | [231.5, 230.1] | 230.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | copytree_top | [3.6, 3.9] | 3.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | verify_1 | [5.1, 5.2] | 5.2 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | setup | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call | [240.2, 239.4] | 239.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | teardown | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper | [235.1, 234.2] | 234.7 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get | [231.5, 230.3] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | flock_ex | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | build | [231.5, 230.3] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | copytree_top | [3.6, 4.0] | 3.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | verify_1 | [5.1, 5.2] | 5.1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | setup | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call | [242.5, 241.3] | 241.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | teardown | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper | [235.4, 234.0] | 234.7 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get | [231.7, 230.1] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | flock_ex | [231.7, 230.1] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | build | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | copytree_top | [3.7, 3.9] | 3.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call_other | [2.3, 2.4] | 2.3 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | verify_1 | [4.9, 4.9] | 4.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | setup | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call | [238.2, 236.9] | 237.6 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | teardown | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper | [235.4, 234.0] | 234.7 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get | [231.7, 230.1] | 230.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | flock_ex | [231.7, 0.0] | 115.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | build | [0.0, 230.1] | 115.1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | copytree_top | [3.7, 3.9] | 3.8 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call_other | [2.8, 2.9] | 2.9 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | setup | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call | [179.9, 178.5] | 179.2 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | teardown | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper | [174.4, 173.0] | 173.7 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get | [171.9, 170.4] | 171.1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | flock_ex | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | build | [171.9, 170.4] | 171.1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | copytree_top | [2.6, 2.6] | 2.6 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper_other | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call_other | [5.4, 5.4] | 5.4 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_1 | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_2 | [0.0, 0.0] | 0.0 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_3 | [0.0, 0.0] | 0.0 | 2 |

| metric | values | median | n |
|---|---|---|---|
| A_model | [327.0, 325.9] | 326.5 | 2 |
| A_residual | [19.9, 19.9] | 19.9 | 2 |
| D_reduce | [7806.6, 7696.8] | 7751.7 | 2 |
| D_split | [8768.0, 8653.4] | 8710.7 | 2 |
| L_reduce | [260.7, 259.5] | 260.1 | 2 |
| L_split | [253.6, 253.1] | 253.4 | 2 |
| call_boundary_other | [0.0, 0.0] | 0.0 | 2 |
| d_defect | [251.0, 249.7] | 250.3 | 2 |
| d_positive | [245.0, 243.9] | 244.5 | 2 |
| mutation_plus_defect_other | [2.1, 2.1] | 2.1 | 2 |
| positive_other | [0.0, 0.0] | 0.0 | 2 |
| reduce_gain_model | [-0.0, 0.0] | -0.0 | 2 |
| reduce_model | [327.0, 325.9] | 326.5 | 2 |
| split_gain_model | [7.0, 6.5] | 6.7 | 2 |
| split_model | [320.0, 319.5] | 319.7 | 2 |

| metric | values | median | n |
|---|---|---|---|
| session_to_first_test | [58.4, 58.3] | 58.3 | 2 |
| execution_interval | [280.5, 279.5] | 280.0 | 2 |
| last_test_to_sessionfinish | [8.2, 8.3] | 8.3 | 2 |
| outer_minus_junit | [1.2, 1.2] | 1.2 | 2 |
| execution_minus_occupancy | [0.0, 0.0] | 0.0 | 2 |

B

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

C

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

## job 内の対差

A−B

| metric | value |
|---|---|
| pairs | [] |
| values | [] |
| median | — |
| n | 0 |
| difference_of_medians | — |
| interpretation | 採用効果は未確立 |
| scope | replica; C is diagnostic, not an upper bound; single-run 10% rule is not a median rule |

A−C

| metric | value |
|---|---|
| pairs | [] |
| values | [] |
| median | — |
| n | 0 |
| difference_of_medians | — |
| interpretation | 採用効果は未確立 |
| scope | replica; C is diagnostic, not an upper bound; single-run 10% rule is not a median rule |

## 歴史照合

| metric | value |
|---|---|
| I | True |
| n_history | 93 |
| n_A | 2 |
| metrics | {"W": {"inside": [true, true], "range": [310.8, 677.1], "percentiles": [0.2, 0.2], "percentiles_percent": [22.6, 22.6], "median_ratio": 0.9}, "O": {"inside": [true, true], "range": [243.8, 578.0], "percentiles": [0.2, 0.2], "percentiles_percent": [24.7, 23.7], "median_ratio": 1.0}, "F": {"inside": [true, true], "range": [65.0, 103.3], "percentiles": [0.2, 0.2], "percentiles_percent": [21.5, 21.5], "median_ratio": 1.0}, "L": {"inside": [true, true], "range": [200.0, 557.7], "percentiles": [0.2, 0.2], "percentiles_percent": [24.7, 23.7], "median_ratio": 1.0}} |
| note | Descriptive inclusion, not equivalence; history rounded to 0.1 seconds. |

## 総括

失敗・未完走・記録失敗は除外。3/3 の同符号は有意差ではない。分割は連続検査、縮約は 3 欠陥型の検出を失う案。実装効果・他 shard への利益は未測定。
