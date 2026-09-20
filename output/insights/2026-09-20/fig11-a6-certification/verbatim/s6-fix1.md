## 所見ごとの対応表

生成器は [plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/tools/plotting/plot_a2_certification.py:654)、test は [test_plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/orchestrator/tests/test_plot_a2_certification.py:1802) を修正しました。

| 所見 | 状態 | 対応箇所・test |
|---|---|---|
| B-1 | closed | `_caption` の A-6 枝に代表 rep 規則を明記。`test_a6_caption_contains_fixed_literals` と `test_a6_caption_excludes_forbidden_words` が検査 |
| B-2 | closed | 同枝で正しさ文を3文に分割し、compile-out／src_token の限定を補足。`test_a6_caption_contains_fixed_literals` が検査 |
| B-3(1) | closed（実装） | `test_landed_fig11_repo_closure_and_caption_when_present` に study／status／effects／median／外部 path 集合の直接照合を追加。着地後の実走は親側 |
| 時刻の出所 | closed | 同枝に `campaign claim recorded at` を追加。固定文 test が検査 |
| 限定2 | closed | 同枝に他条件への外挿禁止文を追加。固定文 test が検査 |

## 実走した検査

| 実行対象 | passed | failed | skipped |
|---|---:|---:|---:|
| `PYTHONPATH=. python3 orchestrator/tests/test_plot_a2_certification.py`：全111 node | 110 | 1 | 0 |
| `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py`：全3 node | 3 | 0 | 0 |
| 収集契約 meta-test：下記3 node の直接呼出し | 3 | 0 | 0 |

唯一の失敗 nodeid は `orchestrator/tests/test_plot_a2_certification.py::test_landed_fig11_repo_closure_and_caption_when_present`。fig11 bundle 未着地による期待赤です。追加した直接照合部分には未到達です。

同モジュールの `test_a6_caption_contains_fixed_literals`、`test_a6_caption_excludes_forbidden_words`、`test_landed_fig11_rejects_all_missing_outputs`、`test_a2_current_full_caption_is_unchanged_for_landed_fig6` を含む残り110件は通過しました。

収集契約は次の nodeid がすべて `DIRECT_CALL_PASS` でした。

- `orchestrator/tests/test_pytest_collection_config.py::test_repo_pytest_ini_has_no_addopts_and_pins_testpaths`
- `orchestrator/tests/test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`
- `orchestrator/tests/test_pytest_collection_config.py::test_ini_testpaths_and_runner_default_target_point_at_the_same_tree`

plain runner の実走 nodeid は次の3件です。

- `orchestrator/tests/test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`
- `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `orchestrator/tests/test_plain_runner_coverage.py::test_this_metatest_is_itself_self_runnable`

指定の実データ再生成は **rc=0**。`probe-fig11/fig11_a6_certification_reject.{png,pdf,provenance.json}` を出力しました。前回 provenance と cells／effects／artist_series／correctness／measurement_conditions／gate_note が一致しました。

| 値 | 前回との一致 |
|---|---|
| median | `10088796` / `9505248` |
| effect | `-0.057841193339621455` |
| abort率 | `0.1547` / `0.145` |

`validate_repo_closure(prov, REPO)` は fig5／fig6／fig7 と scratch fig11 の全件で例外なし。`git diff --check` も rc=0 でした。

新 caption 全文：

> Figure 11. A-6 formal certification attempt a6-20260908b (outer status: reject). The single workload campaign was request 982234.nqsv on bnode031, campaign claim recorded at 2026-09-07T16:29:41.491476+00:00; with one policy workload, the outer status is that workload's verdict itself. The top row shows all five trace-disabled performance samples per cell; short bars are medians, and diamonds with error bars are sample means with t-distribution 95% confidence intervals. The gray dashed line is the workload's no-backoff median and the effect denominator. The median effect copied from certification is read-heavy (rr95) fixed 2 us -5.7841%. M tps means million transactions per second. Mean confidence intervals describe samples; they are not confidence intervals for effects, decisions, or medians, and this artifact makes no significance decision. The displayed outer status is the protocol status based on the predefined median ratio: the adopted cell's median did not exceed the stock cell's median. This is one attempt of five samples per cell; it does not decide a between-run floor exceedance, repeated-attempt reproducibility, or research success or failure, and it does not show that stock is best for read-heavy or that static backoff is harmful for read-heavy in general. The value is not extrapolated to other read ratios, machines, CCBench pins, or concurrency-control protocols. The bottom row is a descriptive leading indicator: one abort-rate observation per cell, taken from the repetition whose throughput is closest to the median (the runner's representative-repetition rule), with no confidence interval and no causal mechanism claim. Correctness comes from separate trace-enabled runs: all 2 cells were certified. This is not a performance certification. The performance reject does not withdraw that correctness evidence. That evidence is limited: L01 limits it to point-key traces; under D1257 the correctness argv was not independently recorded; artifact hashes alone are not compile-out proof (the evidence is source-routed); and src_token equality does not by itself establish semantic identity of the whole translation unit (limitations (i) to (v) of the results note). The raw manifest binds canonical condition-admission records reporting use_class="paper" and admitted=true for all 2 policy cells; the original supply and meaning records are not retained in this artifact. Conditions: 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s, 5 repetitions, CCBench pin 511c953, no perf, trace-disabled performance. The same-sign B-10 read-heavy blocks are a historical concordance under nearby conditions, not an independent reproduction, and are not pooled here; the A-2 attempts measured other workloads and are neither pooled nor compared as before/after.

## 受理・拒否の含意

この fix は生成器の受理集合・拒否条件を変更せず、study／pin／閉包／一意性／axes の検査と `validate_repo_closure` 本体を維持しています。通る正例は実 attempt `a6-20260908b` で、今回も検証から3成果物の出力まで rc=0 で通過しました。

## 所有外への波及

無し。差分と AST 比較で、生成器は `_caption` の A-6 枝だけ、test は指定された3関数だけの変更と確認しました。A-2 枝、suptitle、脚注、correctness 行、その他の test は不変です。

最終変更 path は指定2ソースと `probe-fig11/` の PDF／provenance のみです。PNG は再生成後も差分なしでした。なお、この HEAD では scratch 成果物は既に tracked でした。禁止された git 操作は実行していません。

## 変異事前登録への対応

以下は改訂表への検出 test の対応であり、正式変異走の実測結果ではありません。test 名の接頭辞は `orchestrator/tests/test_plot_a2_certification.py::` です。

| 変異 | 検出 test |
|---|---|
| m0 | 等価 docstring、SURVIVED 想定 |
| m1 | `test_a6_pin_drift_is_rejected` |
| m2 | `test_a6_fixture_loads_as_current_full_with_six_file_closure`、`test_a6_rejects_six_file_closure_underflow_and_overflow` |
| m3 | `test_a6_provenance_tracks_caption_source_with_current_sha`、`test_a6_cli_writes_three_outputs` |
| m4 | `test_layout_rejects_wrong_axes_count` |
| m5 | **`test_a6_caption_contains_fixed_literals`**。新 anchor `This is not a performance certification.` を含む3文を逐語検査。着地後は caption 不一致でも検出 |
| m6a | `test_a6_legacy_profile_is_rejected` |
| m6b | A-6 fixture／caption／layout／CLI／実データ正例 test 群 |
| m7 | `test_current_rejects_duplicate_workload_requests[request_id]`／`[created_utc]` |
| m8 | `test_landed_fig11_rejects_all_missing_outputs` |
| m9 | `test_a2_current_full_caption_is_unchanged_for_landed_fig6` |

## 総括

指定の caption 修正と着地 test の直接照合を実装しました。
主検査は110 passed、未着地による期待赤1件、skipなし。補助6件も通過しました。
実データ再生成 rc=0、主要値と artist は前回一致、fig5/6/7 closure も通過しました。
親側での fig11／README 着地、着地 test・正式変異走、commit が残ります。