実装済み。pytest は未実走、commit なし、docs は未編集です。

編集ファイル:

- [s8c_result_judge.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1352-c07-result-judge/orchestrator/campaign/s8c_result_judge.py:1)（1–1224行）
- [test_s8c_result_judge.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1352-c07-result-judge/orchestrator/tests/test_s8c_result_judge.py:1)（1–668行）

裁定9点との対応:

1. floor は `load_ratified_freeze()` 由来の path、hash、env、head だけで検証し、provenance-only frozen object と専用例外を実装。
2. `judge` は floor 引数を持たず、frozen params と専用の事前登録未発効例外を使用。
3. raw observation から中央値と対差を再導出し、caller の median、delta、rank を拒否。
4. 3条件の完全集合、重複検査、holdout 別 C3、結論の優先順位を実装。
5. predeclared 6 cell 集合を必須引数とし、欠落・余剰・重複を検査。
6. 3表を staging 後に create-only 公開し、絶対 path、repo 外、symlink 解決、失敗時 rollback を実装。
7. validator と exact cell-set 検査の戻り値を judge / publish の実データフローへ接続。
8. owned blob の decoy 非混同をテスト。Unit B の evaluator 配線は所有外のため未変更。
9. 新規2ファイルに禁止 holdout token を含めていない。

テスト nodeid:

- `test_public_names_are_exactly_three`
- `test_owned_result_judge_module_is_not_a_legacy_acceptance_decoy`
- `test_judge_signature_has_no_floor_argument`
- `test_c2_boundary_list_is_documented`（15境界）
- `test_invalid_params_are_preregistration_not_effective`（10境界）
- `test_raw_parameter_mapping_is_not_accepted`
- `test_n_two_uses_sample_sd_denominator_n_minus_one`
- `test_mean_delta_equal_delta_min_is_not_satisfied`
- `test_sample_sd_equal_sd_max_is_satisfied_when_mean_is_strictly_above`
- `test_h1_satisfied_h2_unsatisfied_is_not_hidden_by_one_global_mean`
- `test_condition_id_duplicate_is_rejected_even_when_length_is_three`
- `test_c2_swapped_mapping_boundaries_are_indeterminate`（5境界）
- `test_c3_schedule_and_block_boundaries_are_indeterminate`（5境界）
- `test_c3_replicate_boundaries_are_indeterminate`（3境界）
- `test_c3_does_not_pair_rows_from_different_blocks`
- `test_c3_registered_n_must_match_the_complete_block`（3境界）
- `test_gate_failure_trace_enabled_and_nonfinite_observation_are_indeterminate`
- `test_caller_median_delta_and_rank_fields_are_rejected`
- `test_same_prediction_with_complete_block_is_unsatisfied_not_indeterminate`
- `test_three_condition_conclusion_uses_indeterminate_then_unsatisfied_priority`
- `test_cv_and_diagnostic_values_do_not_enter_status`
- `test_covariance_and_spread_diagnostics_do_not_enter_status`
- `test_source_binding_mismatch_is_indeterminate_not_a_new_status`
- `test_floor_verification_derives_expectations_from_ratified_freeze`
- `test_floor_bytes_mismatch_raises_dedicated_exception`
- `test_floor_bytes_or_floor_value_cannot_change_judge_result`
- `test_publish_creates_three_separate_tables_from_independent_six_cell_set`
- `test_publish_cell_missing_extra_duplicate_leaves_no_table`（3境界）
- `test_publish_rejects_predeclared_set_mutation_without_deriving_it_from_rows`
- `test_publish_requires_absolute_paths_and_excludes_repo`
- `test_publish_is_create_only_and_does_not_overwrite_bytes`
- `test_publish_rejects_symlink_resolving_inside_repo`
- `test_c3_and_c4_boundary_catalogues_are_present`

静的な波及列挙:

- 直接参照は契約 JSON、新規 test、Unit B 所有の `s8c_preregistration_evidence.py` 系。
- `s8c_acceptance_receipt.py`、`trial_registry.py`、旧 `s8b_verdict.py`、`s8b_oracle_judge.py` は現時点で新 judge を import していない。
- 既存共有 fixture は変更していない。
- `test_plain_runner_coverage.py` 対策として新規 test file に plain-runner を追加済み。
- `python3 -m py_compile`、AST 公開名検査、禁止 token 検査、空白検査は実施済み。
- pytest と親 wave の受入検査は未実走であり、親が実施する。

## 総括

- 所有範囲のコードとテストだけを新設した。
- floor 値を judge の入力から排除した。
- C3 は holdout 別の完全 paired block で再計算する。
- 3条件と3表の構造を固定した。
- cell 集合と出力先を fail-closed にした。
- 実装済みだが、pytest は未実走である。