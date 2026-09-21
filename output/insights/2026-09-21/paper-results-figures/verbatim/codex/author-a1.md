## 実装した物

- [生成器](/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/tools/plotting/plot_a1_sized_paired.py): 2 entry の exact attempt 表、attempt 別 loader・caption・CLI・closure を追加。attempt-0002 だけ breach／sd／planned sigma の3行題と図上端の限定文を描画し、使用した表示文字列を provenance に記録します。layout 検査は変更していません。
- [テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/orchestrator/tests/test_plot_a1_sized_paired.py): 指定15本と可視 Text の禁止句・負例テスト1本を追加。既存28本の本文・期待値は byte 一致、既定 fixture の7 file と hash も旧 helper と一致しました。
- `probe-fig14/`: scratch 成果物と実走ログ。untracked のままです。

## 実走した検査

Pegasus `pegasus02` で実行しました。

| 検査 | 結果 | wall |
|---|---|---:|
| A-1 self-run、全44 node | **43 passed / 1 failed / 0 skipped / 0 errors** | 3.098秒 |
| plain-runner coverage、全3 node | 3 passed / 0 failed / 0 skipped | 0.613秒 |
| collection の下記1 node | 1 passed / 0 failed / 0 skipped | 0.312秒 |
| 生成器への `_python_has_perf_predicate` | **False** | 0.033秒 |
| 2 file の `python3 -m py_compile` | rc=0 | 0.126秒 |

全44 nodeid と個別結果は [self-run ログ](/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/probe-fig14/a1-self-run.log) に記録しました。既存28本すべて passed。追加分の nodeid は、以下の名前に `test_plot_a1_sized_paired.py::` を付けたものです。最後の1本だけ failed です。

```text
test_attempt1_default_and_explicit_data_are_identical
test_attempt2_fixture_has_production_shape
test_attempt_hash_key_sets_are_exact
test_attempt2_pinned_input_hashes_match_results_document
test_attempt2_real_leaf_loads_and_matches_results_document
test_attempt2_variance_plan_breach_true_is_accepted
test_attempt2_variance_plan_predicate_mismatch_is_rejected
test_attempt2_caption_contains_fixed_literals_and_breach_values
test_attempt2_caption_avoids_forbidden_claims
test_attempt2_rendered_breach_and_statistics_match_provenance
test_attempt2_real_figure_passes_layout_check
test_attempt2_cli_and_provenance_closure
test_cli_rejects_unknown_attempt_and_hash_options
test_landed_fig14_rejects_missing_or_partial_bundle
test_attempt2_visible_text_forbidden_claims_and_negative_control
test_landed_fig14_repo_closure_and_caption_when_present
```

列挙・命名を扱う meta-test を `rg` で探索し、次を実走しました。

```text
test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted
test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries
test_plain_runner_coverage.py::test_this_metatest_is_itself_self_runnable
test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests
```

attempt-0002 の実描画は suite 1回につき指定どおり4回です。禁止句負例は、正常な panel 題への `reproducibility confirmed` 追加を検出しました。

実データの CLI は両方 **rc=0**。fig14 の成果物：

- [PNG](/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/probe-fig14/fig14_a1_balanced5_sized_attempt2.png)
- [PDF](/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/probe-fig14/fig14_a1_balanced5_sized_attempt2.pdf)
- [provenance.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/probe-fig14/fig14_a1_balanced5_sized_attempt2.provenance.json)

fig9 も `probe-fig14/fig9_a1_balanced5_sized_attempt1.{png,pdf,provenance.json}` を生成しました。着地 provenance との比較は、指定された `generated_utc`／`generator.sha256`／`outputs`／`reproduction` を除き、**全 key 一致、差分0件**です。

fig14 の `validate_repo_closure(prov, worktree_root)` は例外なし。稿 §5.1 の4 pin、§2.1 の mean／h／区間／B／baseline mean／sd／planned sigma／classification／breach は、既存許容差で一致しました。以下は表示用丸め値です。

| workload | mean | h | B | sd | planned sigma | breach |
|---|---:|---:|---:|---:|---:|---|
| write-heavy | 1,538,451.47 | 41,434.21 | 72,952.12 | 80,148.44 | 66,403.45 | true |
| balanced | 548,138.23 | 25,552.38 | 110,832.75 | 49,427.36 | 56,697.44 | false |
| read-heavy | −560,565.60 | 41,746.74 | 305,064.86 | 80,752.99 | 74,668.49 | true |

classification は3 workload とも `resolved-above-floor`。

caption 全文：

> Figure 14. A-1 balanced five-rep paired comparison, sized run attempt-0002 (study paper-story-a1-20260901-balanced5-sized-v1; formal: false; promotion_prohibited: true; result_authority: sized-preregistered-descriptive-only). Columns: write-heavy (rr5, fixed10 minus no-backoff), balanced (rr50, fixed5 minus no-backoff), read-heavy (rr95, fixed2 minus no-backoff), each an independent campaign in its own job (job IDs, respectively: 13220.nqsv, 13221.nqsv, 13222.nqsv; hosts bnode035, bnode039, bnode040). What is drawn: 30 paired differences (variant minus baseline, one per pair index under the balanced five-rep schedule, ten-pair groups in the order A^5 B^5 B^5 A^5 or B^5 A^5 A^5 B^5) as open markers; the arithmetic mean as a solid line with the registered interval mean ± h, h = k·s/√n, k = 2.8315526875186725 (t quantile at 1 − (1/120)/2 with df 29), s the sample standard deviation of the 30 differences; the zero line; and the registered floor boundary ±B, B = 3 % of the baseline-arm mean, as dashed lines. M tps means million transactions per second. Values: write-heavy mean +1.538 M tps (h 0.041 M, B 0.073 M, baseline mean 2.432 M); balanced mean +0.548 M tps (h 0.026 M, B 0.111 M, baseline mean 3.694 M); read-heavy mean -0.561 M tps (h 0.042 M, B 0.305 M, baseline mean 10.169 M). The registered classification is resolved-above-floor in all three workloads (sign positive, positive and negative, respectively). The interval and the classification are the descriptive outputs of the preregistered rule; they are not a hypothesis test and are not a performance certification. This figure reports a single attempt of a non-certified lane: it is not a headline value, no cross-workload conclusion is drawn (preregistration section 7.2), it is not a reproduction of C1, and one attempt does not speak to stability across repeated attempts. Attempt-0001 is neither pooled nor compared with this attempt; no between-attempt difference, ratio, or reproducibility judgment is made. write-heavy: variance_plan_breach=true, sample sd=80,148.44 tps, planned sigma=66,403.45 tps; balanced: variance_plan_breach=false, sample sd=49,427.36 tps, planned sigma=56,697.44 tps; read-heavy: variance_plan_breach=true, sample sd=80,752.99 tps, planned sigma=74,668.49 tps. No cause is attributed to variance_plan_breach. Conditions: Pegasus compute nodes, 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s per repetition, 30 pairs per workload, silo, CCBench pin 511c953, measurement source commit fec4a8187, no perf, trace-disabled performance. Correctness comes from separate trace-enabled verify runs under the recorded legacy check configuration, not the performance configuration: all 6 arms are recorded as certified (result.json correctness_evidence, verify_done frames bound by SHA-256); certified means serializability of the observed YCSB point read/write traces under that check configuration and nothing beyond, and this is not a performance certification. Panel y scales are workload-local and must not be compared across panels. Pilot observations did not enter the estimate; the estimand is the difference under the balanced five-rep schedule, not a carryover-free steady-state effect.

## 未実走・期待赤

- `test_landed_fig14_repo_closure_and_caption_when_present` は **未着地のため赤**。skip／xfail 化していません。
- 変異実走、全受入、pytest、`tools/run_tests.py`、commit 後監査は未実走です。
- 最初の Python 編集コマンドは guard が引用構文を解析できず拒否。構造化パッチで編集を完了しました。検査コマンドの guard 拒否はありません。

## 受理・拒否の含意

変更前は attempt-0001 の固定 leaf のみを受理し、整合した breach=true も拒否する契約でした。正例は既存 `test_real_leaf_loads_and_matches_results_document` です。

変更後は exact pin 表で attempt-0002 も受理し、述語一致を両 attempt に要求したうえで breach=true の scope 拒否を attempt-0001 に限定します。正例は `test_attempt2_variance_plan_breach_true_is_accepted` と実データ実走です。

## 所有外への波及

コード内参照探索では、生成器を実行する所有外 caller／consumer は見つかりませんでした。共有 fixture は変更していません。既存 CLI と fig9 README の再現経路は維持しています。

列挙型 meta-test は上記4 node が通過。追加16 node は通常収集され、裁定 P9 に従い所要時間台帳は未変更です。`git status` の変更は所有2 file と untracked `probe-fig14/` のみ、`git diff --check` は rc=0 でした。

## 変異事前登録への対応

以下は kill 対応の静的確認で、変異実走結果ではありません。nodeid の共通 prefix は `test_plot_a1_sized_paired.py::` です。

| 変異 | 対応 test |
|---|---|
| M0 コメント追加 | `test_generator_comment_change_preserves_provenance_closure`：SURVIVED 予定 |
| M1 attempt1 の breach 拒否除去 | `test_variance_plan_breach_true_is_rejected` |
| M2 attempt2 result pin の1文字変更 | `test_attempt2_pinned_input_hashes_match_results_document` |
| M3 attempt1 caption の1語変更 | `test_landed_fig9_repo_closure_and_caption_when_present` |
| M4 attempt2 の固定限定文除去 | `test_attempt2_caption_contains_fixed_literals_and_breach_values` |
| M5 panel 題の breach 行除去 | `test_attempt2_rendered_breach_and_statistics_match_provenance` |

M1 は policy・統計・hash を整合させて scope 拒否まで到達します。M2 は loader を通さず稿との直接比較で識別します。M3〜M5 も対象の文字列を独立に照合するため、現時点で分割が必要な重複拒否層は見つかりませんでした。M0 の全 suite 比較では、着地前の既知赤1本を baseline として区別する必要があります。

## 総括

実装済み：所有2 file、追加16 test、実データ fig14／fig9 scratch 生成。
検査：43 passed、未着地による期待赤1、skip 0。fig9 provenance は指定範囲で完全一致。
未実走：変異・全受入・commit 後監査。
親への依頼：scratch 退避、fig14 正式生成と README 収録、着地テスト再走、commit。