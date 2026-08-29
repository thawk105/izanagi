# 親の事前実測 — 受入 wall の分解（2026-08-29、既存 artifact のみ）

## 素材

`/work/1/SFC/tanab/.izanagi-acceptance-shards/<group>/shard-N/` に残る full 受入の生 artifact。

- `report.json` (`izanagi-acceptance-shard-report/v1`): `worker_occupancy` = worker → {items, duration_s}、
  `group_to_workers` = xdist_group → [worker]、`terminal_counts`、`effective_scheduler`、
  `worker_collection_digests`、`shard_index`、`shard_count`。
- `junit.xml`: `testsuite@time` = その pytest session の wall（秒）、`testsuite@timestamp`、
  `testsuite@hostname`、`testcase@time` = node 所要（秒）。
  loadgroup に属する node は `testcase@name` の末尾に `@<group>` が付く。

走査対象は 548 group。うち `terminal_counts.passed` 合計 15,000 以上かつ全 shard の report が
揃っているものを full 走とみなし **484 走**を採用した。scheduler は全走 `loadgroup`、worker は全走 48。
K=2 が 293 走、K=3 が 191 走。

再現に使った script は同 job dir の `corpus_scan.py` / `analyze1.py` / `analyze2.py` /
`analyze3.py` / `newest_k3.py`（repo 外、probe）。生出力は `analyze2.txt` / `analyze3.txt` /
`newest_k3.txt`。

## 結果 1 — wall を決めるのは shard-0

484 走のうち **470 走 (97.1%)** で shard-0 が最長。shard-1 が 10 走、shard-2 が 4 走。
以降「critical shard」は各走の最長 shard を指す。

## 結果 2 — wall ≈ 固定床 + 最 busy worker の occupancy

critical shard について、wall を 3 つの説明変数へ単回帰した。

| 母集合 | n | 説明変数 | slope | intercept | r |
|---|---:|---|---:|---:|---:|
| 全体 | 484 | 最 busy worker の occupancy | 1.018 | 75.2 | **0.884** |
| 全体 | 484 | 最長 node の所要 | 0.815 | 158.0 | 0.760 |
| 全体 | 484 | 総 occupancy / worker 数 | 0.747 | 175.0 | 0.649 |
| K=2 | 293 | 最 busy worker の occupancy | 0.983 | 75.3 | **0.965** |
| K=3 | 191 | 最 busy worker の occupancy | 1.455 | 10.7 | 0.837 |
| K=3・08-28 以降 | 117 | 最 busy worker の occupancy | 1.540 | −0.5 | 0.798 |

`wall − max_occ`（テストを 1 本も走らせていない時間の下限）:

| 母集合 | 中央値 | IQR |
|---|---:|---|
| 全体 484 | 70.9 秒 | 65.0 – 78.4 |
| K=2 293 | 67.1 秒 | 63.0 – 74.0 |
| K=3 191 | 74.9 秒 | 70.0 – 87.9 |
| K=3・08-28 以降 117 | 77.3 秒 | 71.9 – 103.3 |

総仕事量ベースの理想値との相関 (r 0.649、K=3 では 0.374) は最 busy worker との相関より一貫して低い。
**受入 wall は総仕事量律速ではなく、最 busy worker 律速である。**

## 結果 3 — 最 busy worker は 2〜5 node しか持たない

critical shard の最 busy worker の item 数分布（全体 484）: 2 が 82 走、3 が 63 走、5 が 58 走、
6 以上は 6 走。最長 node の所要 / 最 busy worker の occupancy の中央値は **0.774**（K=3 では 0.849、
K=3・08-28 以降では 0.838）。

## 結果 4 — critical shard の最長 node は 2 系統に集中する

K=3・08-28 以降 117 走で critical shard の最長 node は:

| 走数 | node |
|---:|---|
| 79 | `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain@s8c-preregistration-candidate` |
| 25 | `test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module` |
| 12 | `test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]` |
| 1 | `test_trial_registry.py::test_t822_acceptance_reports_changed_layer3_snapshot_identity` |

K=3 の直近 40 走のうち 18 走では、最 busy worker の occupancy の **100.0%** が
`s8c-preregistration-candidate` loadgroup（5 node）だけで説明できた。
残り 22 走では最 busy worker が持つのは ungrouped node で、group 単位では帰属できなかった。

## 結果 5 — 100〜130 秒帯に同じ長さの node が並ぶ

直近 K=3 走 (`9c62f3e9`、08-29 02:36、bnode003、shard-0 wall 204.769 秒、6,299 item) の上位 node:

```
126.6  test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module
107.3  test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]
104.7  test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5
100.7  test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes]
 99.5  test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes]
 99.2  test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer]
 99.0  test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28
 98.8  test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff]
 98.6  test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]
 97.4  test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated]
 97.2  test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5
```

この走では `wall − max_occ` = 77.2 秒、最 busy worker = gw46（2 item、127.6 秒）、
総 occupancy / 48 = 101.2 秒。直近 4 走の `wall − max_occ` は 77.2 / 77.7 / 78.9 / 75.4 秒。

## 結果 6 — 走間の所要変動は 1.7 倍に達する

`test_candidate_freeze_matches_contract_and_generation_chain@s8c-preregistration-candidate` の所要は
08-28 22:49 の走で 149.2 秒、08-28 22:40 の走で 213.8 秒、08-29 00:07 の走で 119.4 秒。
走は別々の計算ノード (bnode001/003/007/010/015/018/021/022/047) で実行されており、
混雑度が揃っていない。**同一 tip・同一混雑度での比較にはこの corpus はそのままでは使えない。**

## 既知の限界

- artifact に nodeid → worker の対応が無い。ungrouped node について「critical worker に何が載っていたか」は
  推定である。`tools/acceptance_shards.py` の `_REPORT_WORKERS` は計算されているが report に落ちていない。
- 「テストを走らせていない 70〜77 秒」の内訳は未同定。
- corpus は tip 混成。`worker_collection_digests` で同一 collection universe へ絞り込めるが未実施。
