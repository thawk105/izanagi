## 変更一覧と対応表

変更は指定の2ファイルのみ。`git diff --check` は成功しました。

以下、G = [生成器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl/tools/plotting/plot_b10_static_tail_formal.py)、T = [test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl/orchestrator/tests/test_plot_b10_static_tail_formal.py)。

| 所見 | 状態 | file:line・関数・変更 |
|---|---|---|
| R1 | closed | G:292 `_direct_label`：`min L = {…:.3f}` に変更。他の状態の注記は維持 |
| R3 | closed | G:196 `_load_measurements`：環境検査追加。G:281 `_caption`：Pegasus追加。T:63 `_fixture`：環境追加 |
| R4 | closed | G:285 `_caption`：指定位置に探索走・旧系列の非混合文追加 |
| R6 | closed | G:282 `_caption`：certified の保証範囲を指定文に変更 |
| R7 | closed | T:259 `test_pinned_hashes_are_used_when_no_override`：completion の申告値を production pin に変更し、byte 比較だけで拒否する fixture に修正 |

T:223 `test_caption_contains_fixed_expression_and_certification_literal` に指定の3包含検査も追加しました。禁止句テストは変更していません。partial / regressed はありません。

## 実走結果

指定コマンドを実行しました。

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 orchestrator/tests/test_plot_b10_static_tail_formal.py
rc=1
24 passed, 0 failed, 0 skipped, 1 errors
```

期待赤は次の1件だけです。

```text
orchestrator/tests/test_plot_b10_static_tail_formal.py::test_landed_fig8_repo_closure_and_caption_when_present
ERROR: FigureDataError: artist projection mismatch
```

R1 により保存済み `direct_label` と新しい投影が異なるため、caption 比較より先に拒否されました。親による成果物再生成で解消する対象です。他の赤はありません。

passed の nodeid は共通接頭辞 `orchestrator/tests/test_plot_b10_static_tail_formal.py::` に以下を連結したものです。

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

実データ生成は **rc=0**。生成された注記は workload 順に `min L = 0.304`、`0.299`、`0.274`。PNG・PDF・provenance と一時出力ディレクトリは削除済みです。

## caption 全文

実データ生成の provenance から逐語で転記します。

> Figure 8. B-10 static-backoff right tail, formal cohort of 2026-09-15 (group b10-backoff-grid-20260915T061814Z-545445; aggregate verdict not-observed-in-any-workload; performance_certified: false). Columns show write-heavy (rr5), balanced (rr50) and read-heavy (rr95), each an independent campaign (job IDs, respectively: 0:998865.nqsv, 0:998866.nqsv, 0:998867.nqsv). The x axis shows seven tail points (1250, 1768, 2500, 3535, 5000, 7070 and 9999 us; filled markers) and the 1000 us boundary reference (open marker), measured in the same job but excluded from the interval set. The top row shows means of five trace-disabled repetitions with t-distribution 95% confidence intervals (error bars). M tps means million transactions per second. The bottom row shows abort rates recomputed for each repetition from integer counters as aborts / (aborts + commits), averaged over five repetitions with the same confidence intervals. Segments between adjacent tail points are colored by the interval state copied from the group report: 18/18 intervals (6 per workload) are declining; simultaneous lower bounds L on the per-doubling decrease range from 0.2738 to 0.3704 (Bonferroni over 36 one-sided limits, familywise 0.05). Under the predicates of this preregistration, saturation was not observed up to 9999 us, the representable limit of the current encoding. 9999 us is not a physical limit. From 1250 to 9999 us the mean throughput falls to 0.444, 0.481 and 0.400 of its 1250 us value (write-heavy, balanced, read-heavy) while the abort rate keeps decreasing. This figure is a descriptive accounting of that cost; it makes no mechanism claim and no adoption decision. Conditions: Pegasus compute nodes, 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s, 5 repetitions, silo, CCBench pin 511c953, no perf, trace-disabled performance. Correctness comes from separate trace-enabled runs under the recorded legacy check configuration, not the performance configuration: all 120 records were certified with 0 anomalies; certified means serializability of the observed YCSB point read/write traces under that check configuration and nothing beyond, and this is not a performance certification. Panel heights and slopes use workload-local y scales and must not be compared across panels. This cohort is a different grid and a different cohort from fig2c and is not a continuation of it. No samples from the exploratory run t2418-explore or the t2266-tail series are included; 9999 us was newly measured in this cohort.

## 変異 anchor への影響

author 報告の **M0〜M12 の逐語 anchor に変更はありません**。全13件が現在の生成器にも各1回出現することを確認しました。新しい逐語への置換は不要です。

| anchor | 現在の G 行番号 |
|---|---:|
| M0 | 2 |
| M1 | 36 |
| M2 | 182 |
| M3 | 152 |
| M4 | 301 |
| M5 | 272 |
| M6 | 53 |
| M7 | 229 |
| M8 | 46 |
| M9 | 378 |
| M10 | 139 |
| M11 | 173 |
| M12 | 124 |

M11 の SHA 比較だけをメモリ上で除去して実走し、以下の両 node が `AssertionError: invalid evidence was accepted` で赤になることを確認しました。

- `test_pinned_hashes_are_used_when_no_override`
- `test_external_input_hash_drift_is_rejected`

両方が拒否の消失による kill 証拠です。completion 検査による mask や診断文言差による赤ではありません。最終着地状態の全変異 probe・失敗 node 完全集合の登録は親の担当として残ります。

## 受理集合の変化

入力の受理集合の変更は、各 campaign に **`identity.measurement_env == "pegasus"` を要求する追加だけ**です。実データ3 campaign は検査を通りました。

R7 はテスト fixture の変更のみ。注記・caption の変更は入力の受理条件を変えません。

## 総括

R1・R3・R4・R6・R7 の修正と検証を完了しました。24件成功、着地更新待ちの期待赤1件、回帰なし。実データ生成は成功しました。

docs 編集、repo 内の図再生成、`git add`、commit は行っていません。親による成果物・README 更新と最終変異検証へ引き継げます。
