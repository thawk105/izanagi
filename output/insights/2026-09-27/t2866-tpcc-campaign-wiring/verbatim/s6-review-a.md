## 総括

**NO-GO。静的検査のみで、テスト実測はしていません。**

- 追加された `_PreparedEvaluation.workload` が既存の直接生成 fixture に渡されず、該当テストは `TypeError` になります。
- driver は裁定済みの `pipeline.evaluate` 確認を省略しています。v2 reject の WAL と bench 未起動を実機で示せません。
- driver は実行後に破棄される source root を記録するため、保存した検証記録から同じ source root を再参照できません。
- driver の正常終了条件は job の完了、verify の判定、bench の rc・tps を確認していません。
- 単独性 probe の `demonstrated` は、TPC-C プロセスを `_probe` が検出したことの証明としては不足します。

## 所見

- **RA1 — must-fix** — [test_campaign.py:13734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/tests/test_campaign.py:13734)、[pipeline.py:1263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/pipeline.py:1263)。`_balanced_prepared_fixture` が必須 field `workload` を渡していません。放置すると balanced schedule の回帰テストが実体へ到達せず、bench・COMMIT の検証結果を緑と扱えません。fixture に `workload="ycsb"` を追加してください。

- **RA2 — must-fix** — [smoke_driver_d.py:208](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:208)、[s4-ruling.md](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/s4-ruling.md)。plan v2 が求める `evaluate(..., workload="tpcc")` を省略しています。放置すると campaign 評価単位の実機受理集合と reject WAL が未確認のまま、段の完了記録だけが残ります。独立 layout で R1 を一件評価し、v2 reject と bench 未起動を保存してください。

- **RA3 — must-fix** — [smoke_driver_d.py:78](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:78)、[patchharness.py:346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/patchharness.py:346)。`trace_ccbench_root` は `checkout` の一時 worktree を指し、終了時に削除されます。放置すると freeze・verify 成果物の source root 参照が失効します。source root の pin・digest と再取得手順を記録し、再検証時に有効な root を用意してください。

- **RA4 — must-fix** — [smoke_driver_d.py:201](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:201)。`run_job` は失敗を結果 dict に返せますが、driver は `completed_blocks`、`next_action`、`isolation_*` を検査せず後続へ進みます。verify の status と bench の rc・tps も同様です。放置すると未完了の投入・判定が成功した smoke の台帳になり得ます。各 JSON を保存した後、期待値を満たさなければ非ゼロ終了にしてください。

- **RA5 — should** — [smoke_driver_d.py:130](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:130)、[t2851_transfer_runner.py:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/t2851_transfer_runner.py:342)。`during=False` は composite probe 自体の失敗でも成立します。既知 PID が `pgrep` に見えたことだけでは、TPC-C 検出で `_probe` が拒否したと断定できません。放置すると単独性の実機確認を過大に記録します。composite probe の成功を別に確認したうえで、同じ条件下の pgrep 前後と `_probe` 前後を記録してください。

差分上、perf build の `CCBENCH_TRACE=0`、YCSB の条件付き preimage・key・argv、TPC-C v2 の非認定、anomaly 優先の status に明白な逸脱は見つかりませんでした。TPC-C の bench・COMMIT payload 追加は確認した固定 key 検査と衝突しませんが、実測結果の保証ではありません。

## 変異と test の対応

| 変異 | 殺す test nodeid |
|---|---|
| M1 | `orchestrator/tests/test_campaign.py::test_tpcc_evaluate_v3_reaches_bench_with_workload` |
| M2 | `orchestrator/tests/test_campaign.py::test_tpcc_evaluate_v2_aborts_before_bench_and_builds_tpcc` |
| M3 | `orchestrator/tests/test_calibrator.py::test_measure_point_workload_record_flags_preserve_ycsb_argv` |
| M4 | 同上 |
| M5 | `orchestrator/tests/test_buildcache_v2.py::test_workload_identity_preserves_ycsb_golden_and_separates_tpcc` |
| M6 | 同上 |
| M7 | `orchestrator/tests/test_buildcache_v2.py::test_tpcc_fresh_hit_compiler_target_and_cross_workload_misses` |
| M8 | `orchestrator/tests/test_buildcache_v2.py::test_workload_identity_preserves_ycsb_golden_and_separates_tpcc` |
| M9 | `orchestrator/tests/test_t2851_transfer_runner.py::test_verify_tpcc_s1_real_verifier_v3_v2_and_witness` |
| M10 | 同上 |
| M11 | `orchestrator/tests/test_t2851_transfer_runner.py::test_verify_tpcc_anchor_is_indeterminate[s1-s1-H-pay20]` |
| M12 | `orchestrator/tests/test_t2851_transfer_runner.py::test_verify_tpcc_s1_real_verifier_v3_v2_and_witness` |
| M13 | 同上 |
| M14 | `orchestrator/tests/test_campaign.py::test_tpcc_bench_rejects_duplicate_warehouse_flag` |

M1〜M14 に静的に見て「殺されない」変異はありません。ただし、RA1 のテスト失敗を修正してから実測で確認する必要があります。