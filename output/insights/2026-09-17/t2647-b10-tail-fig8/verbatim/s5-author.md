## 変更一覧

新規2ファイルだけを作成しました。既存ファイルの編集、git add、commit は行っていません。

- [tools/plotting/plot_b10_static_tail_formal.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl/tools/plotting/plot_b10_static_tail_formal.py)（以下 `G`）
- [orchestrator/tests/test_plot_b10_static_tail_formal.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl/orchestrator/tests/test_plot_b10_static_tail_formal.py)（以下 `T`）

生成器の関数・例外一覧：

| file:line | 関数・例外 |
|---|---|
| G:61、65 | `FigureDataError`、`FigureLayoutError` |
| G:69、74、78、83、88、93、98 | `_require`、`_sha256`、`_number`、`_integer`、`_string`、`_close`、`_grid` |
| G:103、136 | `_cell`、`_validate_dat` |
| G:156、166 | `load_measurements`、`_load_measurements` |
| G:257、263、287、295 | `_figure_number`、`_caption`、`_direct_label`、`_artist_series` |
| G:310、368、372、376 | `make_figure`、`_intersection`、`_contains`、`check_figure_layout` |
| G:408、412 | `_display_path`、`build_provenance` |
| G:427、437 | `validate_external_sources`、`validate_repo_closure` |
| G:460、494 | `_publish_outputs`、`main` |

テスト補助関数は T:23 `_load_module`、35 `_hash`、39 `_seal`、49 `_fixture`、107 `_data`、112 `_change_report`、120 `_reject`、414 `_run`。テスト関数は次節に列挙します。

## 実走結果

実行：

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 orchestrator/tests/test_plot_b10_static_tail_formal.py
```

最終結果：**rc=0、24 passed、0 failed、1 skipped、0 errors**。

以下の nodeid はすべて `orchestrator/tests/test_plot_b10_static_tail_formal.py::` を前置したものです。

| T:line | node | 結果 |
|---|---|---|
| 130 | `test_fixture_has_production_shape_and_recomputes_statistics` | passed |
| 151 | `test_artist_series_have_exact_x_and_boundary_reference_is_separate` | passed |
| 175 | `test_interval_states_are_copied_not_recomputed` | passed |
| 197 | `test_real_figure_passes_layout_check` | passed |
| 206 | `test_bbox_overlap_is_a_failure` | passed |
| 222 | `test_caption_contains_fixed_expression_and_certification_literal` | passed |
| 232 | `test_caption_avoids_forbidden_saturation_claims` | passed |
| 240 | `test_caption_figure_number_comes_from_prefix` | passed |
| 247 | `test_external_input_hash_drift_is_rejected` | passed |
| 255 | `test_pinned_hashes_are_used_when_no_override` | passed |
| 260 | `test_performance_certified_true_is_rejected` | passed |
| 265 | `test_verdict_mismatch_is_rejected` | passed |
| 270 | `test_dat_with_missing_row_is_rejected` | passed |
| 278 | `test_dat_abort_rate_disagreeing_with_counters_is_rejected` | passed |
| 290 | `test_boundary_reference_inside_interval_set_is_rejected` | passed |
| 296 | `test_uncertified_correctness_record_is_rejected` | passed |
| 302 | `test_group_id_absent_from_campaign_path_is_rejected` | passed |
| 308 | `test_statistics_mismatch_is_rejected` | passed |
| 314 | `test_pinned_input_hashes_match_results_document` | passed |
| 323 | `test_cli_writes_three_outputs_and_provenance_closure` | passed |
| 349 | `test_cli_rejects_prefix_without_fig_number` | passed |
| 356 | `test_layout_failure_publishes_nothing` | passed |
| 369 | `test_malformed_fields_and_counterpart_mismatches_are_rejected` | passed |
| 389 | `test_real_root_loads_and_matches_results_document_when_present` | passed |
| 402 | `test_landed_fig8_repo_closure_and_caption_when_present` | skipped |

skip 理由は親所有の fig8 bundle と README 記載が未着地のためです。実データ root は読め、読込みテストは実走しています。

初回の目盛り重なりを修正し、45° 回転、境界参照ラベルの段差、`tight_layout` により実寸 Figure が検査を通りました。

実データ生成：

```text
python3 tools/plotting/plot_b10_static_tail_formal.py --measurement-root /work/1/SFC/tanab/b10-backoff-grid-t2500-formal /tmp/t2647-fig8-author-check/fig8_b10_static_tail_not_observed
```

**rc=0**。PNG（165375 bytes）、PDF（27350 bytes）、provenance JSON（336876 bytes）の存在を確認しました。実データの external closure・repo closure も通過し、PNG を目視確認しました。3成果物と一時出力ディレクトリは削除済みです。

`tools/run_tests.py`、pytest、既存テスト群、docs checker、変異 probe は未実走です。

## caption 全文

Figure 8. B-10 static-backoff right tail, formal cohort of 2026-09-15 (group b10-backoff-grid-20260915T061814Z-545445; aggregate verdict not-observed-in-any-workload; performance_certified: false). Columns show write-heavy (rr5), balanced (rr50) and read-heavy (rr95), each an independent campaign (job IDs, respectively: 0:998865.nqsv, 0:998866.nqsv, 0:998867.nqsv). The x axis shows seven tail points (1250, 1768, 2500, 3535, 5000, 7070 and 9999 us; filled markers) and the 1000 us boundary reference (open marker), measured in the same job but excluded from the interval set. The top row shows means of five trace-disabled repetitions with t-distribution 95% confidence intervals (error bars). M tps means million transactions per second. The bottom row shows abort rates recomputed for each repetition from integer counters as aborts / (aborts + commits), averaged over five repetitions with the same confidence intervals. Segments between adjacent tail points are colored by the interval state copied from the group report: 18/18 intervals (6 per workload) are declining; simultaneous lower bounds L on the per-doubling decrease range from 0.2738 to 0.3704 (Bonferroni over 36 one-sided limits, familywise 0.05). Under the predicates of this preregistration, saturation was not observed up to 9999 us, the representable limit of the current encoding. 9999 us is not a physical limit. From 1250 to 9999 us the mean throughput falls to 0.444, 0.481 and 0.400 of its 1250 us value (write-heavy, balanced, read-heavy) while the abort rate keeps decreasing. This figure is a descriptive accounting of that cost; it makes no mechanism claim and no adoption decision. Conditions: 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s, 5 repetitions, silo, CCBench pin 511c953, no perf, trace-disabled performance. Correctness comes from separate trace-enabled runs under the recorded legacy check configuration, not the performance configuration: all 120 records were certified with 0 anomalies, and this is not a performance certification. Panel heights and slopes use workload-local y scales and must not be compared across panels. This cohort is a different grid and a different cohort from fig2c and is not a continuation of it.

## 波及の静的列挙

- `test_plain_runner_coverage.py:60` の全 `test_*.py` 検査対象に入ります。新規テストは `_run()` と `__main__` を持ち、allowlist 追加は不要です。同 :77 の stale/self-runnable allowlist 検査にも追加変更は不要です。
- `orchestrator/tests/README.md:106` 以降の二重 runner 契約に合わせ、tmp_path 注入、PASS・FAIL・ERROR・SKIP の区別を実装しました。pytest 依存と parametrize はありません。
- 共有 fixture、`conftest.py`、既存生成器への import 依存は追加していません。
- consumer は新規テストと親が配置する fig8 bundle・README です。着地テストは部分着地を拒否し、caption の README 包含を検査します。
- results 稿 §4.1 の表を読む pin test が追加されます。文書自体は変更していません。
- `tools/check_docs.py` に今回の新規 Python 2本を直接指定する検査は確認されませんでした。同 :125 は paper-story を追記型記録の対象外として説明しています。親による README 更新後の docs 検査は未実走です。
- 既存図の bytes・provenance・生成器・既存 consumer test は変更していません。

## 受理集合の自己申告

既定 CLI／loader の受理集合を裁定 §5 より広げていません。固定 pin、group、verdict、性能未認証、正しさ認証、格子、反復、DAT 対応、統計の相互検算を実装し、実データ3本を受理しました。

仕様との差分として明記する点：

- **`validate_repo_closure(..., expected_hashes=None)` にも合成 fixture 用 seam を追加しました。** §2.5 の既定固定 pin 検査と、§3 の合成 fixture による closure 成功を両立するためです。CLI から指定できず、既定では固定 pin を使います。テストは合成 provenance が既定 closure では拒否され、実 SHA 注入時だけ通ることを検査します。
- `statistics` は平均に加え、throughput CV・abort CV・abort SD も相互検算します。§2.2 の平均だけを最低要件と解釈する場合、その最低要件より受理集合は狭くなります。
- 45° 回転だけでは近接目盛りの bbox が重なるため、1000 の tick label に追加の段差を設けました。

## 変異 matrix の anchor

対象ファイルはすべて `G`。test node はすべて `T::` を前置します。結果は**予想**であり、変異 probe 未実走です。

| ID | file:line | 逐語 anchor | 単独で殺すと予想する test node |
|---|---|---|---|
| M0 | G:2 | `"""Descriptive B-10 formal static-backoff tail figure and its evidence closure."""` | 等価対照：SURVIVED 予想 |
| M1 | G:36 | `REPORT_DAT: "758b3121cebf7562315a8a70d1f305ced678f90b393fc3cd2a4af87ca0c71c44",` | `test_pinned_input_hashes_match_results_document` |
| M2 | G:182 | `_require(report["performance_certified"] is False, "performance_certified must be false")` | `test_performance_certified_true_is_rejected` |
| M3 | G:152 | `_close(float(rate), a / (a + c), rel=1e-12)` | `test_dat_abort_rate_disagreeing_with_counters_is_rejected` |
| M4 | G:299 | `for kind, xs in (("tail", TAIL_GRID_US), ("boundary-reference", (BOUNDARY_REFERENCE_US,))):` | `test_artist_series_have_exact_x_and_boundary_reference_is_separate` |
| M5 | G:271 | `f"Figure {_figure_number(prefix)}. B-10 static-backoff right tail, formal cohort of 2026-09-15 (group {data['group_id']}; aggregate verdict {data['report']['verdict']}; performance_certified: false).",` | `test_caption_contains_fixed_expression_and_certification_literal` |
| M6 | G:53 | `FIXED_WORDING = "Under the predicates of this preregistration, saturation was not observed up to 9999 us, the representable limit of the current encoding."` | `test_caption_avoids_forbidden_saturation_claims` |
| M7 | G:228 | `intervals = copy.deepcopy(w["intervals"])` | `test_interval_states_are_copied_not_recomputed` |
| M8 | G:46 | `T95_DF4 = 2.7764451051977987` | `test_fixture_has_production_shape_and_recomputes_statistics` |
| M9 | G:376 | `def check_figure_layout(fig, axes):` | `test_bbox_overlap_is_a_failure` |
| M10 | G:139 | `_require(len(lines) - 1 == 120, "dat must contain 120 rows")` | `test_dat_with_missing_row_is_rejected` |
| M11 | G:173 | `_require(digest == hashes[path], f"SHA-256 mismatch: {path}")` | `test_external_input_hash_drift_is_rejected` |
| M12 | G:124 | `_require(payload["certified"] is True, "uncertified correctness record")` | `test_uncertified_correctness_record_is_rejected` |

M3・M10 の負例は変更後の実 SHA と completion を更新しており、pin 不一致に隠れません。M10 の行数検査は、各行の一意なキー・値検査から分離しています。M11 の負例は complete JSON への空白追加で、意味を変えず byte pin だけを検査します。

## 総括

2ファイルの実装と自走検証を完了しました。**24 passed・1 skipped、実データ生成 rc=0、3成果物と閉包を確認済み**です。親による成果物配置、README 更新、変異 probe、統合テスト、commit が残っています。
