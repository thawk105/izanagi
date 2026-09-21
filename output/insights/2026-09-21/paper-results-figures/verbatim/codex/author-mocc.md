## 実装した物

- [生成器](/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/tools/plotting/plot_mocc_witlight_four_arm.py)：5本の固定SHA-256、summary inputsのexact照合、240走の格子・回転・bindings・成功verdict検査、統計再計算、稿と同じ書式を実装。1 axes forest＋数値列、4要素の可視注記、固定7文とConditionsを含むcaptionを生成します。
- [テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/orchestrator/tests/test_plot_mocc_witlight_four_arm.py)：実寸fixture、独立CP/Fisher期待値、入力変異、実artist、layout、禁止句、CLI、二層閉包、実証拠、着地を検査する27本とself-run harnessを新設しました。
- provenanceは指定schemaで、`tracked_inputs`、`external_inputs`、`source_inputs`、`measurement_conditions`、`arms`、`blocks`、`comparisons`、`exposure_ratios`、`artist_series`、`caption`、`outputs`、`reproduction`と生成情報を保持。240走のrecordsは保存しません。
- repo閉包は外部原本を開かず、稿・出力hashと縮約統計からのcaption／artist再構成を検査。外部閉包は5原本から統計・書式・条件を再導出します。保存前layout違反は成果物を公開しません。

## 実走した検査

self-run：**25 passed / 2 failed / 0 skipped / 0 errors、3.863秒**。失敗は未着地の期待赤だけです。

以下はすべて `orchestrator/tests/test_plot_mocc_witlight_four_arm.py::` を接頭辞とする、実走してpassedしたnodeidです。

```text
test_arm_bindings_and_rotation_are_checked
test_caption_fixed_literals_and_forbidden_claims
test_caption_number_comes_from_prefix
test_cli_outputs_and_provenance_closure
test_commit_mean_uses_all_runs_of_each_arm
test_cp95_matches_reference_values_and_boundaries
test_external_hash_drift_is_rejected
test_external_sources_and_repo_closure_have_separate_roots
test_failure_or_indeterminate_is_rejected
test_fisher_is_one_sided_on_lower
test_fixture_has_production_shape_and_rotation
test_landed_fig15_rejects_missing_or_partial_bundle
test_layout_failure_publishes_nothing
test_layout_rejects_overlap_wrong_axes_and_escape
test_production_pins_match_results_document
test_real_evidence_matches_results_document_when_root_present
test_real_figure_passes_layout_check
test_relocated_evidence_keeps_original_input_paths
test_rendered_artists_equal_provenance
test_required_disclosures_are_rendered
test_smoke_or_duplicate_run_in_main_block_is_rejected
test_statistics_recomputed_from_runs
test_summary_disagreement_is_rejected
test_summary_inputs_are_exact
test_summary_inputs_reject_smoke_extra_entry
```

実データCLI：**rc=0、2.561秒**。成果物：

- [PNG](/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/probe-fig15/fig15_mocc_witlight_four_arm.png)
- [PDF](/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/probe-fig15/fig15_mocc_witlight_four_arm.pdf)
- [provenance.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/probe-fig15/fig15_mocc_witlight_four_arm.provenance.json)

稿§2.2／§2.3／§2.6との逐語照合は通過しました。

| arm | k/m | 率 | CP 95% | mean commits per run |
|---|---|---|---|---|
| on / BACK_OFF=0 | 0/60 | 0% | [0%, 5.963%] | 613,741.5 |
| off / BACK_OFF=0 | 1/60 | 1.667% | [0.042%, 8.940%] | 710,659.4 |
| on / BACK_OFF=1 | 0/60 | 0% | [0%, 5.963%] | 788,885.6 |
| off / BACK_OFF=1 | 1/60 | 1.667% | [0.042%, 8.940%] | 933,621.8 |

両比較とも片側Fisherは`0.500`。on/off曝露比はBACK_OFF=0が`0.8636`、BACK_OFF=1が`0.8450`。scratch provenanceの`validate_repo_closure`／`validate_external_sources`はともに例外なしでした。PNGも目視確認しました。

追加検査：

| 検査 | 結果 |
|---|---|
| `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` | PASS |
| 同 `test_allowlist_has_no_stale_or_self_runnable_entries` | PASS |
| 同 `test_this_metatest_is_itself_self_runnable` | PASS |
| `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`（関数直接実行） | PASS、0.479秒 |
| 新規2ファイルの`py_compile` | rc=0 |
| 新生成器への`_python_has_perf_predicate` | `False` |

plain-runner meta-testは合計3 passed／0 failed／0 skipped、コマンド所要1.261秒。guardによる拒否はありませんでした。

caption全文：

> Figure 15. Stock MOCC lightweight witness observations: G2 signal detection rates with two-sided 95% Clopper–Pearson (CP) intervals and descriptive mean commits per run. e9-witlight-wit (on / BACK_OFF=0): 0/60, 0%, CP [0%, 5.963%], mean commits per run 613,741.5. e9-witlight-nowit (off / BACK_OFF=0): 1/60, 1.667%, CP [0.042%, 8.940%], mean commits per run 710,659.4. e9-witlight-wit-bo1 (on / BACK_OFF=1): 0/60, 0%, CP [0%, 5.963%], mean commits per run 788,885.6. e9-witlight-nowit-bo1 (off / BACK_OFF=1): 1/60, 1.667%, CP [0.042%, 8.940%], mean commits per run 933,621.8. Primary comparison BACK_OFF=0: one-sided Fisher (on lower), unadjusted p = 0.500; on/off exposure ratio 0.8636. Secondary comparison BACK_OFF=1: one-sided Fisher (on lower), unadjusted p = 0.500; on/off exposure ratio 0.8450. G2 signal locations: W1 e9-witlight-nowit (1/15); W3 e9-witlight-nowit-bo1 (1/15). Non-significance does not establish equivalence, and zero detections do not establish absence. Power 0.105 is a calculation under the design assumptions, not a measured quantity: independent Bernoulli trials, 60 runs per arm, off probability 0.0417, on probability 0, and a one-sided Fisher test at alpha 0.05. TRACE=1 commit counts are exposure, not performance. G2 signals do not identify a root cause or distinguish a real anomaly from a torn read. This is a non-certifying observation; individual verifier certified flags and observational_only=false do not certify this wave, MOCC, or the witness. The denominator includes only 4 blocks x 15 rounds x 4 arms; smoke runs are excluded. CP intervals and Fisher p values assume independent Bernoulli trials and do not model within-node dependence, rotation order, or temporal variation. The discriminator was not reached: no on-arm G2 signals occurred, so it fired zero times and made zero comparisons. Detection rates are per fixed-time 3 s run, not a comparison at equal commit exposure. Values from earlier waves [T-1892], [T-2774], and [T-2779] are neither pooled nor compared here. Conditions: 48 threads, 10,000 records, Zipf 0.9, read ratio 50, rmw 0, max operations 10, 3 s, TRACE=1 build, pin e9e477ca + X/P + witlight patches, Pegasus compute nodes, 4 blocks W1–W4 x 15 rounds x 4 arms, smoke excluded.

可視Text一覧（数値列は上の表の各行・各セルをそのまま描画）：

```text
Stock MOCC lightweight witness: G2 signal detection
G2 signal detection rate (%)
0
2
4
6
8
10
on / BACK_OFF=0
off / BACK_OFF=0
on / BACK_OFF=1
off / BACK_OFF=1
k/m
Rate
CP 95%
mean commits per run
0/60
0%
[0%, 5.963%]
613,741.5
1/60
1.667%
[0.042%, 8.940%]
710,659.4
0/60
0%
[0%, 5.963%]
788,885.6
1/60
1.667%
[0.042%, 8.940%]
933,621.8
BACK_OFF=0: on/off exposure ratio 0.8636
BACK_OFF=1: on/off exposure ratio 0.8450
non-certifying; TRACE=1 build
Commits: exposure, not performance
BACK_OFF=0: one-sided Fisher (on lower, unadjusted) p = 0.500
BACK_OFF=1: one-sided Fisher (on lower, unadjusted) p = 0.500
Not significant is not equivalence; power 0.105 is calculated under design assumptions.
G2 signal: verifier detection; does not identify a root cause.
```

## 未実走・期待赤

以下の2本は**未着地のため赤**です。skip／xfailにはしていません。

```text
orchestrator/tests/test_plot_mocc_witlight_four_arm.py::test_landed_fig15_repo_closure_and_caption_when_present
orchestrator/tests/test_plot_mocc_witlight_four_arm.py::test_landed_fig15_external_closure_when_root_present
```

全受入、pytest経由のmeta-test全体、変異実走は未実施です。`test_pytest_collection_config.py`は関連する列挙検査1本を直接実行しました。台帳被覆検査はP9の親裁定を採用し、再実走していません。

## 受理・拒否の含意

受理するのは、CLIでは指定5本の固定bytes、test seamでは同じ格子・条件・観測範囲を満たし、再計算結果とsummaryが一致する再封印fixtureです。

拒否するのは、hash／入力目録／格子／回転／bindings／verdict／集計が不一致の入力、または閉包・layoutが破れた成果物です。

正例として、commit数が非一様な240走fixtureがロード・CLI描画・二層閉包を通過しました。

## 所有外への波及

既存caller・共有fixture・consumerの変更は無し。既存Python内に新生成器への参照は無く、他生成器のimportもありません。

列挙型への影響は、新testファイルと27 nodeの追加です。plain-runner検査と除外集合検査は通過、所要時間台帳は未登録です。`git status`に現れた追加は所有する2ファイルと`probe-fig15/`だけで、すべてuntrackedです。Git変更操作、docs・output・外部証拠への編集は行っていません。

## 変異事前登録への対応

以下はkill担当の対応であり、変異実走結果ではありません。nodeidの接頭辞はすべて`orchestrator/tests/test_plot_mocc_witlight_four_arm.py::`です。

| 変異 | kill担当test |
|---|---|
| M6 summary pin変更 | `test_production_pins_match_results_document` |
| M7 summary inputs照合除去 | `test_summary_inputs_reject_smoke_extra_entry` |
| M8 CP上側分位変更 | `test_cp95_matches_reference_values_and_boundaries` |
| M9 Fisher両側化 | `test_fisher_is_one_sided_on_lower` |
| M10 commit平均の分母240化 | `test_commit_mean_uses_all_runs_of_each_arm` |
| M11 可視not performance削除 | `test_required_disclosures_are_rendered` |
| M12 題へequivalent追加 | `test_caption_fixed_literals_and_forbidden_claims` |
| M13 保存前layout検査除去 | `test_layout_failure_publishes_nothing` |

M7はsummaryを再封印し、loaderだけで判定するためhash／repo閉包との重複拒否を避けています。M10はsummaryに存在しないcommit平均を独立総和で検査。M13は正常データと実Figureに重なりだけを加えます。登録された局所変異について、分割が必要な重複拒否層は見つかりませんでした。

## 総括

実装済み：生成器・27テスト・scratchの3成果物。
実走：25 passed、期待赤2、skip 0；実データrc=0、二層閉包通過。
未実走：全受入・変異実走。
親への依頼：scratch退避、正式fig15生成、README収録、着地2テストの再実走とcommit。