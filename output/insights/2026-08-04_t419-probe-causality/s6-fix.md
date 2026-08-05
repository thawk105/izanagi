実装を完了しました。因果閾値は変更せず、実験成立条件と実行包絡を fail-closed に強化しています。docs 編集・commit・pytest 実行はしていません。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| R1-1 | closed | contrast だけが偽になる 45/48 の M1 専用 fixture を追加 |
| R1-2 | closed | oracle を pytest 側へ移し、定数・境界・median・NaN/inf・空 vector を固定 |
| R1-3 | closed | A1 の 48×5、pin/reader、anchor、pin_order permutation を validity 化 |
| R1-4 | closed | child PID・affinity・liveness・tick・wait 証拠から介入状態を再計算 |
| R1-5 | closed | parser 3/3 match、band 検証、解析例外の INVALID 化 |
| R1-6 | closed | PID+starttime と未帰属 `/proc/stat` tick による純粋競合判定を追加 |
| R1-7 | closed | A2/A3 nested 母集団と flat reads の同一性を検査し、sham を should-pass に追加 |
| R1-8 | closed | 合計445を assert し、manifest provenance に事前登録数を記録 |
| R1-9 | closed | A2 各 condition 後に実測1秒 cooldown を記録 |
| R1-10 | closed | exception-only、detector-side M5、should-reject 局所 M6 の検出 node を追加 |
| R2-1 | closed | 系列内 PID走査を除去し、固定 monotonic deadline と `late` を実装 |
| R2-2 | closed | instrumentation・child開始後の block/condition anchor に変更 |
| R2-3 | closed | active child解除を反映し、競合 arm 後の後続 arm を停止 |
| R2-4 | closed | unavailable/error/mismatch/3件未満をすべて INVALID 化 |
| R2-5 | closed | create-only log/rc、manifest後のatomic result、最後のdone-markerを実装 |
| R2-6 | closed | HEAD・driver/PBS/calibration hash、関連dirty、queue/projectを投入時束縛 |
| R2-7 | closed | outer child registry と期限付きTERM→KILL→再waitを実装 |
| R2-8 | closed | PBS 20分、driver 900秒 alarm、arm別所要時間を実装 |

### 変更ファイル

- [t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py) — 3,125行
- [t419_probe_causality.pbs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.pbs) — 179行
- [test_t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py) — 430行

既存テスト node の期待値変更: **0件**。段5の既存8 node名と期待結果は維持しています。

### テスト node 完全列挙

```text
test_preregistered_threshold_literals_are_pinned
test_preregistered_primary_read_total_is_445
test_default_hard_deadline_is_900_seconds
test_no_effect_is_refuted
test_all_out_of_band_is_not_confirmed
test_paired_contrast_only_fixture_kills_m1
test_pinned_hit_rate_boundary_0p95_is_inclusive
test_nonpinned_rate_boundary_0p05_is_inclusive
test_positive_contrast_boundary_46_is_inclusive
test_band_endpoints_are_inclusive
test_even_length_median_is_arithmetic_middle
test_nonfinite_observed_values_fail_closed
test_nonfinite_calibration_values_are_rejected
test_empty_vectors_fail_closed
test_in_band_non_nominal_uses_canonical_band
test_alpha_converges_by_positional_cumulative_minimum
test_positive_paired_contrast_can_confirm
test_invalid_fixtures_are_not_evaluated[missing_cpu]
test_invalid_fixtures_are_not_evaluated[child_evidence_missing]
test_invalid_fixtures_are_not_evaluated[child_status_mismatch]
test_invalid_fixtures_are_not_evaluated[exception_only]
test_invalid_fixtures_are_not_evaluated[band_missing]
test_invalid_fixtures_are_not_evaluated[parser_unavailable]
test_invalid_fixtures_are_not_evaluated[population_missing]
test_missing_reads_is_invalid_and_not_evaluated
test_contention_invalidates_execution_and_verdict
test_a1_missing_anchor_is_invalid
test_a1_pin_order_must_be_allocated_permutation
test_a3_flat_reads_must_equal_nested_blocks
test_a2_flat_reads_must_equal_nested_conditions
test_a3_block_population_must_be_complete
test_quiet_block_anchor_is_required
test_a2_condition_cooldown_is_required
test_a3_contention_anchor_must_follow_busy_child_barrier
test_parser_crosscheck_requires_three_matching_files
test_parser_crosscheck_nonmatch_statuses_are_invalid[unavailable]
test_parser_crosscheck_nonmatch_statuses_are_invalid[error]
test_parser_crosscheck_nonmatch_statuses_are_invalid[mismatch]
test_invalid_bands_return_invalid_not_evaluated[none]
test_invalid_bands_return_invalid_not_evaluated[reversed]
test_invalid_bands_return_invalid_not_evaluated[nan]
test_causal_analysis_exception_becomes_invalid
test_method_table_includes_a2_sham_in_should_pass_population
test_should_pass_fixtures_are_not_overrejected
test_should_reject_rows_are_not_replaced_by_constant_reject
test_short_lived_competitor_is_detected_from_unattributed_ticks
test_attributed_self_ticks_do_not_create_competition
test_released_child_pid_reuse_is_not_allowlisted
```

### 検査結果

- `python3.10 -m py_compile ...`: rc=0
- `bash -n t419_probe_causality.pbs`: rc=0
- 純計算 `--self-test`: rc=0、16 fixture
- pytest: **0件**（ログインノード禁止のため未実行）
- docs編集: 0件
- commit: 0件

qsub caller は `EXPECT_HEAD`、3種のSHA256、`T419_QUEUE`、`T419_PROJECT` を渡す必要があります。collector は `result.json` 単体でなく、`manifest.json`・`probe.rc`・`done-marker` の整合を採用条件にしてください。

## 総括

- closed 18 / partial 0 / regressed 0。
- 因果閾値 0.95 / 0.05 / 46 と canonical band は不変。
- 残リスクは、未帰属 kernel tick による意図的な過剰 INVALID と実機での deadline 遅延率。
- 親は計算ノードで全48 pytest node、変異matrix、PBS self-test→実験→finalizeを実測すること。
- 実機では read開始間隔・`late`、anchor時系列、cooldown実時間、child回収証拠を確認すること。
- `.o/.e`、qstat会計、wrapper rc、manifest、done-markerの最終照合は親の作業として残る。