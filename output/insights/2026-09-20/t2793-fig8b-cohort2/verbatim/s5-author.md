## 変更の要約

指定の 2 ファイルだけを変更しました。commit は作成していません。

- [生成器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2793-unit-impl/tools/plotting/plot_b10_static_tail_formal.py)：純増 **163 行**。
  - `COHORTS` と `load_measurements(..., cohort=1)`：役割・group・path・pin を固定し、両 cohort に同じ拒否条件を適用。
  - `_draw_block` / `make_figure_v2`：7.2 × 10.6 in、4 行 × 3 列、見出し 2 個、凡例 1 個。
  - `_caption_v2` / `_artist_series_v2` / `build_provenance_v2`：cohort ごとの記録・射影を保持。
  - `_validate_repo_closure_v2`：位置ごとの役割、pin、出力 hash、射影、固定 key 集合、非プール条件を検査。
  - `check_figure_layout` / `_publish_outputs` / `main`：12 axes・見出し侵入検査と `--reproduction-cohort 2` を接続。
- [test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2793-unit-impl/orchestrator/tests/test_plot_b10_static_tail_formal.py)：純増 **242 行**。
  - `_fixture` / `_seal` を cohort 対応。
  - `_fixture_pair` と新規 12 test を追加。

両ファイルとも規模上限内です。

## v1 不変の確認

- `_caption`、`_artist_series`、`build_provenance` は HEAD と関数本文が完全一致。
- closure v1 は、入口の v2 dispatch を除いて本文が完全一致。
- 既存 25 test と `_run()` の本文も完全一致。
- 既定 fixture の JSON・DAT・complete の bytes と seal は旧 fixture と一致。
- 実データの再生成で、v1 caption・artist 射影が着地 fig8 と一致。
- v1 展開 argv は従来の 5 要素を保持。英字 suffix は v1 で拒否。
- 着地 fig8 の 3 ファイルは着手前後で SHA-256 が一致：

```text
png         24eab2e8b96db14a570b8ee0efc158cdceeb4913f4787030eccd9326d98cbb2a
pdf         11071b72995c43da39b7309c94e6935fac498e36979e3d4f912e7194634948ff
provenance  3ccdb0aa147660d261e8aad395695549a556a76fd9aef5595223681185b7b6d2
```

## 新 test 一覧

以下の node 名の共通接頭辞は `test_plot_b10_static_tail_formal.py::` です。変異欄は独立した検出根拠の対応であり、変異 runner の実測結果ではありません。

| test 名 | 独立した根拠・対象変異 | 実走 |
|---|---|---|
| `test_cohort2_pinned_hashes_match_cohort2_results_document` | 凍結稿 §4.1 の digest：M1 | PASS |
| `test_cohort_roles_are_fixed_literals` | 役割 literal と `is False`：M2・M10 | PASS |
| `test_cohort2_rejects_alternate_verdict_and_certification_failures` | 指定 verdict を投入・再 seal。性能認証、未認証、anomaly も拒否：M3 | PASS |
| `test_figure_number_suffix_is_v2_only` | `fig8b_` の v2 受理・v1 拒否：M8 | PASS |
| `test_v2_caption_contains_independent_fixed_wording` | 定数参照ではない逐語 assertion・禁止語検査：M4・M5 | PASS |
| `test_two_cohort_artists_match_raw_repetitions_and_intervals` | 生 reps から平均・CI を計算し、両 block の tail・境界点・区間線・直接ラベルと比較：M9 | PASS |
| `test_v2_block_title_intrusion_publishes_nothing` | panel 内へ見出しを移動し、侵入エラーと成果物ゼロ：M6・M7 | PASS |
| `test_v2_text_overlap_publishes_nothing` | 重なりエラーと成果物ゼロ：M6 | PASS |
| `test_cli_cohort2_writes_three_outputs_and_v2_closure` | CLI 実経路、3 成果物、argv、drift 拒否、非プール負例。入替後に再射影して位置検査を独立化：M11 | PASS |
| `test_cli_rejects_reproduction_cohorts_one_and_three` | CLI 1・3 の `SystemExit(2)` と成果物ゼロ | PASS |
| `test_landed_fig8b_repo_closure_and_both_captions_when_present` | 着地 closure・README の両 caption | SKIP：未着地 |
| `test_real_root_loads_cohort2_and_matches_results_document_when_present` | 実入力、24 cell、992686.2、比 0.445 / 0.484 / 0.398 と稿 | PASS |

M0 は等価対照として残しています。

## 実走結果

実行ホストは **pegasus02**。repo root で実行しました。

```text
python3 orchestrator/tests/test_plot_b10_static_tail_formal.py
36 passed, 0 failed, 1 skipped, 0 errors
rc=0
```

新規 node の結果は上表のとおりです。既存 node は以下すべて PASS。同じ共通接頭辞 `test_plot_b10_static_tail_formal.py::` を持ちます。

```text
test_artist_series_have_exact_x_and_boundary_reference_is_separate
test_bbox_overlap_is_a_failure
test_boundary_reference_inside_interval_set_is_rejected
test_caption_avoids_forbidden_saturation_claims
test_caption_contains_fixed_expression_and_certification_literal
test_caption_figure_number_comes_from_prefix
test_cli_rejects_prefix_without_fig_number
test_cli_writes_three_outputs_and_provenance_closure
test_dat_abort_rate_disagreeing_with_counters_is_rejected
test_dat_with_missing_row_is_rejected
test_external_input_hash_drift_is_rejected
test_fixture_has_production_shape_and_recomputes_statistics
test_group_id_absent_from_campaign_path_is_rejected
test_interval_states_are_copied_not_recomputed
test_landed_fig8_repo_closure_and_caption_when_present
test_layout_failure_publishes_nothing
test_malformed_fields_and_counterpart_mismatches_are_rejected
test_performance_certified_true_is_rejected
test_pinned_hashes_are_used_when_no_override
test_pinned_input_hashes_match_results_document
test_real_figure_passes_layout_check
test_real_root_loads_and_matches_results_document_when_present
test_statistics_mismatch_is_rejected
test_uncertified_correctness_record_is_rejected
test_verdict_mismatch_is_rejected
```

実 root を使った CLI 実走：

| mode | 一時 prefix | 結果 |
|---|---|---|
| v1 | `/tmp/fig8_t2793_probe` | rc=0、PNG・PDF・provenance、layout・closure 通過 |
| v2 | `/tmp/fig8b_t2793_probe` | rc=0、PNG・PDF・provenance、layout・closure 通過 |

v2 caption 冒頭：

> Figure 8b. B-10 static-backoff right tail: primary result, formal cohort 1 of 2026-09-15 …

続いて両 group・verdict・事前登録 commit と `performance_certified: false for both cohorts.` が入ります。PNG も目視しました。

pytest は **未実走**です。`tools/run_tests.py … -q -rf` は `qstat -Q` preflight rc=1 により runner rc=16、`child_started=false` で終了しました。自動生成された dispatch 一時ファイルは除去済みです。`git diff --check` は通過しました。

## 波及

- 静的検索では、所有外 Python caller・共有 fixture・consumer test の参照はありませんでした。
- `_fixture` / `_seal` の変更はこの test ファイル内に限定され、既定挙動を保持しています。
- 文書側の参照は plotting README、figures README、paper-story の版・results 稿にあります。変更していません。
- fig8b 成果物と README 収録は親の統合作業として残しています。

## 未了・懸念

- 変異 matrix の probe / final は未実走です。
- fig8b 着地 test は未着地のため skip。統合後の実走が必要です。
- 投稿寸法での PDF 可読性・1 ページ収録は未確認です。
- closure は記録の再射影検査であり、原入力からの完全な再監査ではありません。描画値は別途、生 reps に基づく test で検証しています。

## 総括

author の 2 ファイル実装は完了しました。既存 25 test を保持し、自走 harness と実データの両 mode が通過しています。docs・着地成果物・commit は作成していません。