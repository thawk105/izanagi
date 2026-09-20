## 所見の対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| A-N1 | closed | [test:605](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2793-unit-impl/orchestrator/tests/test_plot_b10_static_tail_formal.py:605) に production pin 拒否 assertion を追加。対象 node PASS |
| B-N1 | closed | 検索で定義のみと確認後、`PRIMARY_COHORT` を削除。[生成器:52](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2793-unit-impl/tools/plotting/plot_b10_static_tail_formal.py:52)。修正後の検索は0件 |
| 親 nit | closed | [生成器:448](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2793-unit-impl/tools/plotting/plot_b10_static_tail_formal.py:448) の見出し y と axes bottom を調整。実データの layout 検査・PNG 目視で余白を確認 |

## 変更の要約

指定2ファイルのみ、3行追加・3行削除です。

- 下 block 見出し y：`.49 → .475`
- axes bottom：`(.78, .57, .31, .12) → (.79, .59, .30, .12)`
- figsize：7.2 × 10.6 in、axes 高さ：.13 を維持
- 既存期待値、fixture、caption、layout 検査は変更なし

## 実走結果

`pegasus02`、repo root から指定の自走 harness を実行。**rc=0、36 passed / 1 skipped / 0 failed / 0 errors**。pytest は未実走です。

以下の node はすべて `orchestrator/tests/test_plot_b10_static_tail_formal.py::` 配下です。

```text
PASS test_artist_series_have_exact_x_and_boundary_reference_is_separate
PASS test_bbox_overlap_is_a_failure
PASS test_boundary_reference_inside_interval_set_is_rejected
PASS test_caption_avoids_forbidden_saturation_claims
PASS test_caption_contains_fixed_expression_and_certification_literal
PASS test_caption_figure_number_comes_from_prefix
PASS test_cli_cohort2_writes_three_outputs_and_v2_closure
PASS test_cli_rejects_prefix_without_fig_number
PASS test_cli_rejects_reproduction_cohorts_one_and_three
PASS test_cli_writes_three_outputs_and_provenance_closure
PASS test_cohort2_pinned_hashes_match_cohort2_results_document
PASS test_cohort2_rejects_alternate_verdict_and_certification_failures
PASS test_cohort_roles_are_fixed_literals
PASS test_dat_abort_rate_disagreeing_with_counters_is_rejected
PASS test_dat_with_missing_row_is_rejected
PASS test_external_input_hash_drift_is_rejected
PASS test_figure_number_suffix_is_v2_only
PASS test_fixture_has_production_shape_and_recomputes_statistics
PASS test_group_id_absent_from_campaign_path_is_rejected
PASS test_interval_states_are_copied_not_recomputed
PASS test_landed_fig8_repo_closure_and_caption_when_present
SKIP test_landed_fig8b_repo_closure_and_both_captions_when_present
PASS test_layout_failure_publishes_nothing
PASS test_malformed_fields_and_counterpart_mismatches_are_rejected
PASS test_performance_certified_true_is_rejected
PASS test_pinned_hashes_are_used_when_no_override
PASS test_pinned_input_hashes_match_results_document
PASS test_real_figure_passes_layout_check
PASS test_real_root_loads_and_matches_results_document_when_present
PASS test_real_root_loads_cohort2_and_matches_results_document_when_present
PASS test_statistics_mismatch_is_rejected
PASS test_two_cohort_artists_match_raw_repetitions_and_intervals
PASS test_uncertified_correctness_record_is_rejected
PASS test_v2_block_title_intrusion_publishes_nothing
PASS test_v2_caption_contains_independent_fixed_wording
PASS test_v2_text_overlap_publishes_nothing
PASS test_verdict_mismatch_is_rejected
```

SKIP 理由は親所有の fig8b 成果物が未着地のためです。

実 root で次を実行し、**rc=0**。PNG・PDF・provenance を `/tmp` に生成しました。

```bash
python3 tools/plotting/plot_b10_static_tail_formal.py \
  --measurement-root /work/1/SFC/tanab/b10-backoff-grid-t2500-formal \
  /tmp/fig8b_t2793_fix1 --reproduction-cohort 2
```

`check_figure_layout(fig, axes, expected_axes=12)` は通過し、`block-title` の侵入なし。[生成 PNG](/tmp/fig8b_t2793_fix1.png) も目視確認済みです。

figure 座標で見出し y は **上 .955／下 .475**。全12 axes の bbox は以下の組合せです（形式：`x, y, width, height`）。

| 行 | 左列 x | 中列 x | 右列 x | y | width | height |
|---|---:|---:|---:|---:|---:|---:|
| cohort 1 上段 | .095000 | .421649 | .748298 | .790 | .236702 | .130 |
| cohort 1 下段 | .095000 | .421649 | .748298 | .590 | .236702 | .130 |
| cohort 2 上段 | .095000 | .421649 | .748298 | .300 | .236702 | .130 |
| cohort 2 下段 | .095000 | .421649 | .748298 | .120 | .236702 | .130 |

下 block 見出し bbox と上 block の x ラベル間の余白は **.041974（約32.0 pt）**、下 block 上段の panel title との間は **.027704（約21.1 pt）**です。

## 波及

変更は指定2ファイルのみ。docs・repo 内成果物の書込み、commit はしていません。`git diff --check` は通過しました。

## 総括

nit 3件を closed としました。今回の実走で退行は検出されていません。親側の fig8b 着地検証は未了です。