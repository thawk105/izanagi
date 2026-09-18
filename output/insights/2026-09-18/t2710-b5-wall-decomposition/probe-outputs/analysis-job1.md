## 対象と定義

replica shard-0 の同一 tip 反復。受入証跡ではない。model は下限参考値。

走数 6、採用 6。中央値は各走を分解した後、指標別に計算。

W=JUnit testsuite、L=JUnit testcase 最大、O=phase 合算最大、F=W−O、P=O−L、D=全 phase 合算。

## shard 表

| condition | run | host | ordinal | W | O | O_production | O_difference | F | L | longest_node | P | longest_on_busy | D | mean_load | busy_worker | busy_count | terminal | outer_wall | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | job1-01-S1 | bnode027 | 1 | 135.3 | 132.1 | — | — | 3.2 | 132.1 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 0.0 | True | 132.1 | 132.1 | gw0 | 1 | {"selected": 1, "executed_selected": 1, "finished": 1, "failed": 0, "skipped": 0, "rc": 0} | 135.8 | 採用 |
| S | job1-02-S | bnode027 | 2 | 138.3 | 130.5 | — | — | 7.9 | 130.5 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 0.0 | True | 1187.5 | 108.0 | gw1 | 1 | {"selected": 11, "executed_selected": 11, "finished": 11, "failed": 0, "skipped": 0, "rc": 0} | 138.8 | 採用 |
| S1 | job1-03-S1 | bnode027 | 3 | 127.6 | 124.5 | — | — | 3.1 | 124.5 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | -0.0 | True | 124.5 | 124.5 | gw0 | 1 | {"selected": 1, "executed_selected": 1, "finished": 1, "failed": 0, "skipped": 0, "rc": 0} | 128.1 | 採用 |
| S | job1-04-S | bnode027 | 4 | 148.5 | 140.6 | — | — | 7.9 | 140.6 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 0.0 | True | 1298.6 | 118.1 | gw1 | 1 | {"selected": 11, "executed_selected": 11, "finished": 11, "failed": 0, "skipped": 0, "rc": 0} | 149.9 | 採用 |
| S1 | job1-05-S1 | bnode027 | 5 | 128.8 | 125.7 | — | — | 3.1 | 125.7 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | -0.0 | True | 125.7 | 125.7 | gw0 | 1 | {"selected": 1, "executed_selected": 1, "finished": 1, "failed": 0, "skipped": 0, "rc": 0} | 139.9 | 採用 |
| S | job1-06-S | bnode027 | 6 | 137.6 | 129.5 | — | — | 8.0 | 129.5 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 0.0 | True | 1175.8 | 106.9 | gw1 | 1 | {"selected": 11, "executed_selected": 11, "finished": 11, "failed": 0, "skipped": 0, "rc": 0} | 138.9 | 採用 |

## job1-01-S1

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 132.1 | 1789699278.8 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw0 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 132.1 | 0.0 | 107.1 | 104.8 | 0.0 | 104.8 | 0.0 | 2.3 | [4.9, 4.6, 4.5, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |

配布確認

| metric | value |
|---|---|
| worker | gw0 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 132.1}] |
| second | — |
| initial_second_predicted | — |
| initial_second_observed_matches | — |
| third_or_later | False |
| collection_matches | {"gw0": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 1.9 |
| execution_interval | 132.1 |
| last_test_to_sessionfinish | 1.3 |
| outer_minus_junit | 0.5 |
| execution_minus_occupancy | 0.0 |
| close_spans | [{"run_id": "job1-01-S1", "condition": "S1", "nodeid": "", "worker": "gw0", "pid": 892407, "phase": "session", "event": "close", "span_id": "892407:18", "parent_span_id": null, "t_start": 1789699411.1, "t_end": 1789699412.1, "monotonic_start": 243029.7, "monotonic_end": 243030.7, "call_index": 1, "outcome": "ok", "extra": {"base_path": "/tmp/izanagi-t080-e2e-session-d3d612150a2126fd02e92f5b6f278f42ddbde47a6394de805e6726c5ad01be52"}}] |
| (省略: 1749 bytes の行。原本は job dir analysis/job1/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw0": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

## job1-02-S

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 130.5 | 1789699419.3 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw0 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 124.0 | 0.0 | 105.4 | 101.8 | 0.0 | 101.8 | 0.0 | 3.6 | [0.0, 4.9, 4.6, 4.5] | 0.0 | 4.6 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw2 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 114.8 | 0.0 | 105.3 | 101.7 | 101.7 | 0.0 | 0.0 | 3.5 | [4.9, 4.6] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw4 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 110.2 | 0.0 | 105.3 | 101.7 | 101.7 | 0.0 | 0.0 | 3.5 | [4.9, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw1 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 130.5 | 0.0 | 105.3 | 101.7 | 101.7 | 0.0 | 0.0 | 3.5 | [5.0, 4.6, 4.5, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 110.2 | 0.0 | 105.3 | 101.7 | 101.7 | 0.0 | 0.0 | 3.5 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 105.4 | 0.0 | 105.3 | 101.7 | 101.7 | 0.0 | 0.0 | 3.5 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw7 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 110.3 | 0.0 | 105.4 | 101.8 | 0.0 | 101.8 | 0.0 | 3.6 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw8 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 110.3 | 0.0 | 105.4 | 101.8 | 0.0 | 101.8 | 0.0 | 3.6 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw3 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 112.3 | 0.0 | 105.3 | 101.7 | 101.7 | 0.0 | 0.0 | 3.5 | [4.9] | 0.0 | 2.1 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 107.9 | 0.0 | 105.3 | 101.7 | 0.0 | 101.7 | 0.0 | 3.5 | [] | 0.0 | 2.7 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw10 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 51.5 | 0.0 | 44.7 | 42.3 | 0.0 | 42.3 | 0.0 | 2.4 | [0.0, 0.0, 0.0] | 0.0 | 6.8 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw1 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 130.5}] |
| second | — |
| initial_second_predicted | — |
| initial_second_observed_matches | — |
| third_or_later | False |
| collection_matches | {"gw1": null, "gw0": null, "gw2": null, "gw3": null, "gw4": null, "gw5": null, "gw6": null, "gw7": null, "gw8": null, "gw9": null, "gw10": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 2.5 |
| execution_interval | 130.5 |
| last_test_to_sessionfinish | 5.3 |
| outer_minus_junit | 0.5 |
| execution_minus_occupancy | 0.0 |
| (省略: 4804 bytes の行。原本は job dir analysis/job1/analysis.md) |
| (省略: 18896 bytes の行。原本は job dir analysis/job1/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw0": 0.0, "gw1": 0.0, "gw10": 0.0, "gw2": 0.0, "gw3": 0.0, "gw4": 0.0, "gw5": 0.0, "gw6": 0.0, "gw7": 0.0, "gw8": 0.0, "gw9": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

## job1-03-S1

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 124.5 | 1789699561.4 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw0 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 124.5 | 0.0 | 99.4 | 97.2 | 0.0 | 97.2 | 0.0 | 2.3 | [4.9, 4.6, 4.5, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |

配布確認

| metric | value |
|---|---|
| worker | gw0 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 124.5}] |
| second | — |
| initial_second_predicted | — |
| initial_second_observed_matches | — |
| third_or_later | False |
| collection_matches | {"gw0": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 1.9 |
| execution_interval | 124.5 |
| last_test_to_sessionfinish | 1.2 |
| outer_minus_junit | 0.5 |
| execution_minus_occupancy | 0.0 |
| close_spans | [{"run_id": "job1-03-S1", "condition": "S1", "nodeid": "", "worker": "gw0", "pid": 901459, "phase": "session", "event": "close", "span_id": "901459:18", "parent_span_id": null, "t_start": 1789699686.0, "t_end": 1789699687.0, "monotonic_start": 243304.7, "monotonic_end": 243305.7, "call_index": 1, "outcome": "ok", "extra": {"base_path": "/tmp/izanagi-t080-e2e-session-6f3168452452e1b5eba94b1dd795d54199d3513d36a9c91fa7fedbb959e8ca04"}}] |
| (省略: 1749 bytes の行。原本は job dir analysis/job1/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw0": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

## job1-04-S

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 140.6 | 1789699694.2 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw0 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 134.2 | 0.0 | 115.6 | 112.1 | 0.0 | 112.1 | 0.0 | 3.6 | [0.0, 4.9, 4.6, 4.5] | 0.0 | 4.6 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw2 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 125.0 | 0.0 | 115.5 | 111.9 | 111.9 | 0.0 | 0.0 | 3.6 | [5.0, 4.6] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw4 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 120.5 | 0.0 | 115.5 | 111.9 | 111.9 | 0.0 | 0.0 | 3.6 | [5.0, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw1 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 140.6 | 0.0 | 115.5 | 111.9 | 111.9 | 0.0 | 0.0 | 3.6 | [5.0, 4.6, 4.5, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 120.4 | 0.0 | 115.5 | 111.9 | 111.9 | 0.0 | 0.0 | 3.6 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 115.6 | 0.0 | 115.5 | 111.9 | 111.9 | 0.0 | 0.0 | 3.6 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw7 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 120.5 | 0.0 | 115.5 | 112.0 | 0.0 | 112.0 | 0.0 | 3.6 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw8 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 120.6 | 0.0 | 115.6 | 112.1 | 0.0 | 112.1 | 0.0 | 3.6 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw3 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 122.5 | 0.0 | 115.5 | 111.9 | 111.9 | 0.0 | 0.0 | 3.6 | [4.9] | 0.0 | 2.1 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 118.2 | 0.0 | 115.5 | 111.9 | 0.0 | 111.9 | 0.0 | 3.6 | [] | 0.0 | 2.7 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw10 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 60.5 | 0.0 | 54.8 | 52.5 | 0.0 | 52.5 | 0.0 | 2.3 | [0.0, 0.0, 0.0] | 0.0 | 5.6 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw1 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 140.6}] |
| second | — |
| initial_second_predicted | — |
| initial_second_observed_matches | — |
| third_or_later | False |
| collection_matches | {"gw1": null, "gw0": null, "gw2": null, "gw3": null, "gw4": null, "gw5": null, "gw6": null, "gw7": null, "gw8": null, "gw9": null, "gw10": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 2.5 |
| execution_interval | 140.6 |
| last_test_to_sessionfinish | 6.3 |
| outer_minus_junit | 1.3 |
| execution_minus_occupancy | 0.0 |
| (省略: 4804 bytes の行。原本は job dir analysis/job1/analysis.md) |
| (省略: 18896 bytes の行。原本は job dir analysis/job1/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw0": 0.0, "gw1": 0.0, "gw10": 0.0, "gw2": 0.0, "gw3": 0.0, "gw4": 0.0, "gw5": 0.0, "gw6": 0.0, "gw7": 0.0, "gw8": 0.0, "gw9": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

## job1-05-S1

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 125.7 | 1789699847.6 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw0 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 125.7 | 0.0 | 100.6 | 98.3 | 0.0 | 98.3 | 0.0 | 2.3 | [4.9, 4.6, 4.5, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | — | not executed | — | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | [] | 0.0 | 0.0 | 0 | 0 |

配布確認

| metric | value |
|---|---|
| worker | gw0 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 125.7}] |
| second | — |
| initial_second_predicted | — |
| initial_second_observed_matches | — |
| third_or_later | False |
| collection_matches | {"gw0": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 1.9 |
| execution_interval | 125.7 |
| last_test_to_sessionfinish | 11.9 |
| outer_minus_junit | 11.1 |
| execution_minus_occupancy | 0.0 |
| close_spans | [{"run_id": "job1-05-S1", "condition": "S1", "nodeid": "", "worker": "gw0", "pid": 910094, "phase": "session", "event": "close", "span_id": "910094:18", "parent_span_id": null, "t_start": 1789699973.5, "t_end": 1789699974.5, "monotonic_start": 243592.1, "monotonic_end": 243593.1, "call_index": 1, "outcome": "ok", "extra": {"base_path": "/tmp/izanagi-t080-e2e-session-93f7831dcabe1d21215963d17e5e9e02ac712b3715bfd0efb2678ba99e9f3982"}}] |
| (省略: 1749 bytes の行。原本は job dir analysis/job1/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw0": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

## job1-06-S

最忙 worker の item 列（start 順）

| nodeid | duration | start |
|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 129.5 | 1789699992.3 |

M node 成分（実行していない node は not executed）

| nodeid | worker | status | base_key | setup | call | teardown | helper | get | flock_ex | build | get_other | copytree_top | verify | helper_other | call_other | helper_count | verify_count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | gw0 | observed | ["AI-Agent: none", false, true, true] | 0.0 | 123.1 | 0.0 | 104.5 | 100.9 | 0.0 | 100.9 | 0.0 | 3.6 | [0.0, 4.9, 4.6, 4.5] | 0.0 | 4.6 | 1 | 4 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | gw2 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 113.9 | 0.0 | 104.4 | 100.8 | 100.8 | 0.0 | 0.0 | 3.6 | [4.9, 4.6] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | gw4 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 109.3 | 0.0 | 104.4 | 100.8 | 100.8 | 0.0 | 0.0 | 3.6 | [4.9, 0.0] | 0.0 | 0.0 | 1 | 2 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | gw1 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 129.5 | 0.0 | 104.4 | 100.8 | 100.8 | 0.0 | 0.0 | 3.6 | [5.0, 4.6, 4.5, 4.5, 4.5] | 0.0 | 2.1 | 1 | 5 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | gw5 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 109.3 | 0.0 | 104.4 | 100.8 | 100.8 | 0.0 | 0.0 | 3.6 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | gw6 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 104.4 | 0.0 | 104.4 | 100.8 | 100.8 | 0.0 | 0.0 | 3.6 | [] | 0.0 | 0.1 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | gw7 | observed | ["AI-Agent: codex", false, true, false] | 0.0 | 109.4 | 0.0 | 104.4 | 100.9 | 0.0 | 100.9 | 0.0 | 3.6 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | gw8 | observed | ["AI-Agent: none", true, true, false] | 0.0 | 109.4 | 0.0 | 104.5 | 100.9 | 0.0 | 100.9 | 0.0 | 3.6 | [4.9] | 0.0 | 0.0 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | gw3 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 111.4 | 0.0 | 104.4 | 100.8 | 100.8 | 0.0 | 0.0 | 3.6 | [4.9] | 0.0 | 2.1 | 1 | 1 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | gw9 | observed | ["AI-Agent: none", false, true, false] | 0.0 | 107.0 | 0.0 | 104.4 | 100.8 | 0.0 | 100.8 | 0.0 | 3.6 | [] | 0.0 | 2.7 | 1 | 0 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | gw10 | observed | ["AI-Agent: none", false, false, false] | 0.0 | 49.0 | 0.0 | 43.7 | 41.4 | 0.0 | 41.4 | 0.0 | 2.3 | [0.0, 0.0, 0.0] | 0.0 | 5.3 | 1 | 3 |

配布確認

| metric | value |
|---|---|
| worker | gw1 |
| units | [{"scope": "orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]", "cost": 240.0, "items": ["orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]"], "duration": 129.5}] |
| second | — |
| initial_second_predicted | — |
| initial_second_observed_matches | — |
| third_or_later | False |
| collection_matches | {"gw0": null, "gw1": null, "gw2": null, "gw3": null, "gw4": null, "gw5": null, "gw6": null, "gw7": null, "gw8": null, "gw9": null, "gw10": null} |
| initial_second_inference | Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not. |

固定費 3 層・close（未分離項を含む）

| metric | value |
|---|---|
| session_to_first_test | 2.5 |
| execution_interval | 129.5 |
| last_test_to_sessionfinish | 6.4 |
| outer_minus_junit | 1.3 |
| execution_minus_occupancy | 0.0 |
| (省略: 4804 bytes の行。原本は job dir analysis/job1/analysis.md) |
| (省略: 18896 bytes の行。原本は job dir analysis/job1/analysis.md) |
| unseparated | worker start/collection/prewarm; shutdown/JUnit; post-session cleanup |

観測 overhead 感度

| metric | value |
|---|---|
| worker_H_proxy | {"gw0": 0.0, "gw1": 0.0, "gw10": 0.0, "gw2": 0.0, "gw3": 0.0, "gw4": 0.0, "gw5": 0.0, "gw6": 0.0, "gw7": 0.0, "gw8": 0.0, "gw9": 0.0} |
| busy_worker_H_proxy | 0.0 |
| controller_report_seconds | 0.0 |
| controller_H_proxy | 0.0 |
| note | Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound. |

## 条件別中央値と全走の値

S1

| metric | values | median | n |
|---|---|---|---|
| W | [135.3, 127.6, 128.8] | 128.8 | 3 |
| O | [132.1, 124.5, 125.7] | 125.7 | 3 |
| F | [3.2, 3.1, 3.1] | 3.1 | 3 |
| L | [132.1, 124.5, 125.7] | 125.7 | 3 |
| P | [0.0, -0.0, -0.0] | -0.0 | 3 |
| D | [132.1, 124.5, 125.7] | 125.7 | 3 |
| mean_load | [132.1, 124.5, 125.7] | 125.7 | 3 |
| outer_wall | [135.8, 128.1, 139.9] | 135.8 | 3 |

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
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call | [132.1, 124.5, 125.7] | 125.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper | [107.1, 99.4, 100.6] | 100.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get | [104.8, 97.2, 98.3] | 98.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | build | [104.8, 97.2, 98.3] | 98.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | copytree_top | [2.3, 2.3, 2.3] | 2.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call_other | [2.1, 2.1, 2.1] | 2.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_1 | [4.9, 4.9, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_2 | [4.6, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_3 | [4.5, 4.5, 4.5] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_4 | [4.5, 4.5, 4.5] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_5 | [4.5, 4.5, 4.5] | 4.5 | 3 |
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
| session_to_first_test | [1.9, 1.9, 1.9] | 1.9 | 3 |
| execution_interval | [132.1, 124.5, 125.7] | 125.7 | 3 |
| last_test_to_sessionfinish | [1.3, 1.2, 11.9] | 1.3 | 3 |
| outer_minus_junit | [0.5, 0.5, 11.1] | 0.5 | 3 |
| execution_minus_occupancy | [0.0, 0.0, 0.0] | 0.0 | 3 |

S

| metric | values | median | n |
|---|---|---|---|
| W | [138.3, 148.5, 137.6] | 138.3 | 3 |
| O | [130.5, 140.6, 129.5] | 130.5 | 3 |
| F | [7.9, 7.9, 8.0] | 7.9 | 3 |
| L | [130.5, 140.6, 129.5] | 130.5 | 3 |
| P | [0.0, 0.0, 0.0] | 0.0 | 3 |
| D | [1187.5, 1298.6, 1175.8] | 1187.5 | 3 |
| mean_load | [108.0, 118.1, 106.9] | 108.0 | 3 |
| outer_wall | [138.8, 149.9, 138.9] | 138.9 | 3 |

M 成分の中央値と全値（各 node/指標を個別集計）

| nodeid | metric | values | median | n |
|---|---|---|---|---|
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call | [124.0, 134.2, 123.1] | 124.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper | [105.4, 115.6, 104.5] | 105.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get | [101.8, 112.1, 100.9] | 101.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | build | [101.8, 112.1, 100.9] | 101.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | copytree_top | [3.6, 3.6, 3.6] | 3.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | call_other | [4.6, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_1 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_2 | [4.9, 4.9, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_3 | [4.6, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5 | verify_4 | [4.5, 4.5, 4.5] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call | [114.8, 125.0, 113.9] | 114.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper | [105.3, 115.5, 104.4] | 105.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | flock_ex | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | copytree_top | [3.5, 3.6, 3.6] | 3.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | verify_1 | [4.9, 5.0, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes] | verify_2 | [4.6, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call | [110.2, 120.5, 109.3] | 110.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper | [105.3, 115.5, 104.4] | 105.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | flock_ex | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | copytree_top | [3.5, 3.6, 3.6] | 3.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | verify_1 | [4.9, 5.0, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes] | verify_2 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call | [130.5, 140.6, 129.5] | 130.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper | [105.3, 115.5, 104.4] | 105.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | flock_ex | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | copytree_top | [3.5, 3.6, 3.6] | 3.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | call_other | [2.1, 2.1, 2.1] | 2.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_1 | [5.0, 5.0, 5.0] | 5.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_2 | [4.6, 4.6, 4.6] | 4.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_3 | [4.5, 4.5, 4.5] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_4 | [4.5, 4.5, 4.5] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | verify_5 | [4.5, 4.5, 4.5] | 4.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call | [110.2, 120.4, 109.3] | 110.2 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper | [105.3, 115.5, 104.4] | 105.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | flock_ex | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | copytree_top | [3.5, 3.6, 3.6] | 3.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2] | verify_1 | [4.9, 4.9, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call | [105.4, 115.6, 104.4] | 105.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper | [105.3, 115.5, 104.4] | 105.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | flock_ex | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | copytree_top | [3.5, 3.6, 3.6] | 3.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5 | call_other | [0.1, 0.1, 0.1] | 0.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call | [110.3, 120.5, 109.4] | 110.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper | [105.4, 115.5, 104.4] | 105.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get | [101.8, 112.0, 100.9] | 101.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | build | [101.8, 112.0, 100.9] | 101.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | copytree_top | [3.6, 3.6, 3.6] | 3.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer] | verify_1 | [4.9, 4.9, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call | [110.3, 120.6, 109.4] | 110.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper | [105.4, 115.6, 104.5] | 105.4 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get | [101.8, 112.1, 100.9] | 101.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | build | [101.8, 112.1, 100.9] | 101.8 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | copytree_top | [3.6, 3.6, 3.6] | 3.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | call_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff] | verify_1 | [4.9, 4.9, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call | [112.3, 122.5, 111.4] | 112.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper | [105.3, 115.5, 104.4] | 105.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | flock_ex | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | build | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | copytree_top | [3.5, 3.6, 3.6] | 3.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | call_other | [2.1, 2.1, 2.1] | 2.1 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated] | verify_1 | [4.9, 4.9, 4.9] | 4.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call | [107.9, 118.2, 107.0] | 107.9 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper | [105.3, 115.5, 104.4] | 105.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | build | [101.7, 111.9, 100.8] | 101.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | copytree_top | [3.5, 3.6, 3.6] | 3.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28 | call_other | [2.7, 2.7, 2.7] | 2.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | setup | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call | [51.5, 60.5, 49.0] | 51.5 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | teardown | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper | [44.7, 54.8, 43.7] | 44.7 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get | [42.3, 52.5, 41.4] | 42.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | flock_ex | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | build | [42.3, 52.5, 41.4] | 42.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | get_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | copytree_top | [2.4, 2.3, 2.3] | 2.3 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | helper_other | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | call_other | [6.8, 5.6, 5.3] | 5.6 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_1 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_2 | [0.0, 0.0, 0.0] | 0.0 | 3 |
| orchestrator/tests/test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7 | verify_3 | [0.0, 0.0, 0.0] | 0.0 | 3 |

| metric | values | median | n |
|---|---|---|---|

| metric | values | median | n |
|---|---|---|---|
| session_to_first_test | [2.5, 2.5, 2.5] | 2.5 | 3 |
| execution_interval | [130.5, 140.6, 129.5] | 130.5 | 3 |
| last_test_to_sessionfinish | [5.3, 6.3, 6.4] | 6.3 | 3 |
| outer_minus_junit | [0.5, 1.3, 1.3] | 1.3 | 3 |
| execution_minus_occupancy | [0.0, 0.0, 0.0] | 0.0 | 3 |

A

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
| I | False |
| n_history | 93 |
| n_A | 0 |
| metrics | {"W": {"inside": [], "range": [310.8, 677.1], "percentiles": [], "percentiles_percent": [], "median_ratio": null}, "O": {"inside": [], "range": [243.8, 578.0], "percentiles": [], "percentiles_percent": [], "median_ratio": null}, "F": {"inside": [], "range": [65.0, 103.3], "percentiles": [], "percentiles_percent": [], "median_ratio": null}, "L": {"inside": [], "range": [200.0, 557.7], "percentiles": [], "percentiles_percent": [], "median_ratio": null}} |
| note | Descriptive inclusion, not equivalence; history rounded to 0.1 seconds. |

## 総括

失敗・未完走・記録失敗は除外。3/3 の同符号は有意差ではない。分割は連続検査、縮約は 3 欠陥型の検出を失う案。実装効果・他 shard への利益は未測定。
