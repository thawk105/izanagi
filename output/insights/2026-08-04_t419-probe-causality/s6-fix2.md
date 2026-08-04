実装を完了しました。編集は指定された3ファイルのみで、docs 編集・commit・pytest 実行はありません。既存テスト node の期待値変更・削除・skip・緩和は 0 件です。

変更ファイル:

- [t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py) — 3,551行
- [t419_probe_causality.pbs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.pbs) — 201行
- [test_t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py) — 682行

### G-1〜G-9

| 項目 | 状態 | 対応 |
|---|---|---|
| G-1 | closed | process tickをuser+nice+system+guestに限定、CPU別residual、PID+starttime帰属、三値attribution、UNRESOLVEDのVALID維持、COMPETITOR後続停止を実装 |
| G-2 | closed | 98/102と97.999/102.001を外部literalで固定し、bandの数式的一致を検査 |
| G-3 | closed | seedからpermutationを再計算し、pin_order・by_pin・flat 5件群の順序を検査 |
| G-4 | closed | child算術・starttime同一性、busy≥5、sham≤1、INCONCLUSIVE 3/8 gateを実装 |
| G-5 | closed | validityをtotal化し、mode型不正、非有限・非正MHz、異常なtop-level型をreason化 |
| G-6 | closed | nestedを持たないA4 29/30の単一理由fixtureを追加 |
| G-7 | closed | JSONをprobe_rcへ改名し、wrapper.rc→done-marker順を実装。done-markerなしは不採用と明記 |
| G-8 | closed | finalizationでHEAD・driver・PBS・較正・env_attestation hashとdirtyを再照合。scheduler envはmatch/mismatch/unavailableで記録 |
| G-9 | closed | lateness_nsと50% interval閾値によるlateを実装 |

### 焦点再レビュー18項

| 所見 | 状態 | 根拠 |
|---|---|---|
| R1-1 | closed | paired contrast fixtureを維持 |
| R1-2 | closed | G-2 |
| R1-3 | closed | G-3 |
| R1-4 | closed | G-4 |
| R1-5 | closed | G-5 |
| R1-6 | closed | G-1。IRQ誤検知とCPU横断相殺を除去 |
| R1-7 | closed | nested/flat同一性とsham should-passを維持 |
| R1-8 | closed | 445件の定数・assert・manifest束縛を維持 |
| R1-9 | closed | condition後1秒cooldownを維持 |
| R1-10 | closed | G-6によりM2a専用fixtureを追加 |
| R2-1 | closed | PID scan後置を維持し、恒真lateもG-9で是正 |
| R2-2 | closed | instrumentation/barrier後anchorを維持 |
| R2-3 | closed | COMPETITORのみ後続停止、UNRESOLVEDは継続 |
| R2-4 | closed | parser 3/3 match gateを維持 |
| R2-5 | partial | probe_rc・wrapper.rc・done順は閉鎖。.o/.e・会計receiptは親裁定どおり親作業 |
| R2-6 | closed | G-8 |
| R2-7 | closed | bounded TERM→KILL→waitを維持 |
| R2-8 | closed | 900秒driver・20分PBS・arm durationを維持 |

### 追加テスト node

追加21定義、parametrize展開で24 nodeです。

```text
test_child_threshold_literals_are_pinned
test_band_formula_external_oracle_literals
test_band_must_equal_median_plus_or_minus_tolerance_formula
test_a4_primary_count_gate_has_a_single_reason_fixture
test_execution_validity_is_total_for_non_string_condition_mode
test_execution_validity_rejects_nonfinite_mhz_with_one_reason
test_execution_validity_is_total_for_unexpected_top_level_types[none]
test_execution_validity_is_total_for_unexpected_top_level_types[integer]
test_execution_validity_is_total_for_unexpected_top_level_types[list]
test_execution_validity_is_total_for_unexpected_top_level_types[string]
test_a1_pin_order_and_flat_groups_match_seed_permutation
test_a1_sorted_order_is_rejected_even_when_it_is_a_permutation
test_child_tick_delta_must_match_start_end_arithmetic
test_child_pid_starttime_identity_must_remain_stable
test_sham_above_one_tick_is_inconclusive
test_two_inconclusive_a2_pairs_keep_arm_valid
test_three_inconclusive_a2_pairs_invalidate_arm
test_irq_and_softirq_only_ticks_are_clean
test_unpinned_reader_migration_is_unresolved_but_valid
test_residual_above_self_unattributable_invalidates_and_stops_later_arms
test_positive_nonself_pid_delta_is_competitor_snapshot_evidence
test_late_uses_half_read_interval_threshold
test_scheduler_binding_unavailable_is_recorded_not_rejected
test_scheduler_binding_mismatch_is_explicit
```

既存 node の期待値変更: **0件**。既存 node の削除・改名: **0件**。

### 検査結果

- `python3.10 -m py_compile ...`: rc=0
- `bash -n tools/pegasus/probes/t419_probe_causality.pbs`: rc=0
- 純計算 `--self-test`: rc=0、17 fixture
- pytest: **0件**（Pegasusログインノード禁止のため未実行）
- docs編集: 0件
- commit: 0件

qsub callerには新たに `EXPECT_ENV_ATTESTATION_SHA256` が必要です。collectorは `result.json`、`manifest.json`、`probe.rc`、`wrapper.rc`、`done-marker`の整合を確認し、done-marker欠落を必ず不採用にしてください。

## 総括

- 焦点18項は closed 17 / partial 1 / regressed 0、G-1〜G-9は closed 9 / partial 0 / regressed 0。
- 0.95 / 0.05 / 46 / 445、canonical band、`INVALID ⇒ NOT_EVALUATED` は不変。
- 残リスクは実機でのPID snapshot精度、tick丸め、scheduler env名の可用性、finalization race。
- R2-5の残りは親所有の `.o/.e`・最終qstat・会計receipt化。
- 親は計算ノードで全pytest node、変異matrix、PBS wrapperとfinal hash raceを確認すること。
- 実機ではUNRESOLVED継続、COMPETITOR後続停止、child 5/1 tick、wrapper.rc→done順を確認すること。