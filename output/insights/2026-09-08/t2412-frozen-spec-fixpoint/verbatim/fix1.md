## 直した内容

- [test_floor_pair_driver.py:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:310): `_install_git` に `spec_relpath` 引数を追加。
- [test_floor_pair_driver.py:321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:321): 模擬 `diff-tree` 出力を `os.fsencode(spec_relpath) + b"\0"` から生成。
- [test_p3_b4_floor_artifact_issuer.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:66): issuer fixture が実際の `"refs/spec.json"` を渡すよう修正。

## 変更後の挙動

`spec.json` を使う既存 driver fixture は従来どおり受理され、issuer の `refs/spec.json` も模擬 changed-path と一致して producer loader を通過します。異なる path、余分な path、明示した不正な `changed_paths_stdout` の拒否条件は変更していません。

## 実走した検査

- `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py`: runner rc=16、dispatch preflight 失敗で未実走。
- `...::test_identity_is_not_a_caller_surface_and_missing_protocol_is_named`: runner rc=16、同じく未実走。
- AST parse: rc=0。
- `git diff --check`: rc=0。

状態は **実装済み・未実走** です。queue state は観測不能、dispatch child は開始されませんでした。

## 波及可能性

リポジトリ全体を静的検索し、他ファイルからの呼び出しはありませんでした。同一 driver test 内の直接呼び手は以下です。

- helpers: `_prepare_spec`、`_prepare_configured_spec`、`_run_multi_pair_sample_production`
- tests: `test_loader_rejects_v2_schema_on_v3_shaped_spec`、`test_every_schema_field_is_required`、`test_d1641_failure_policy_is_the_only_accepted_wire_policy`、`test_frozen_pair_statistics_require_exact_module_constants`、`test_mutation_01_unknown_key_is_rejected_only_by_exact_loader`、`test_removed_claim_only_schema_fields_are_rejected_as_unknown`、`test_mutation_02_valid_spec_with_wrong_expected_sha256_is_rejected`、`test_mutation_03_head_blob_byte_mismatch_is_rejected`、`test_blob_queries_use_the_once_resolved_loaded_head`、`test_tracked_calibration_declared_sha_mismatch_is_rejected_for_sha_only`、`test_nonfinite_and_duplicate_json_are_rejected`、`test_type_bool_range_and_nested_unknown_keys_fail_closed`、`test_loader_rejects_symlink_and_checkout_escape`、`test_mutation_04_calibration_projection_gates_have_single_reason_inputs`、`test_mutation_14_rejected_calibration_is_rejected_for_quality_only`、`test_mutation_15_calibration_records_mismatch_is_rejected_for_records_only`、`test_calibration_none_mode_rejection_is_explicit_and_intentional`、`test_build_receipt_binary_sha_and_trace_mutations_fail_closed`、`test_mutation_16_probe_command_is_not_a_spec_field`、`test_mutation_19_source_commit_must_equal_loaded_head_only_parent`、`test_mutation_20_extra_env_cannot_control_path_resolution`、`test_pair_owns_artifact_references_and_requires_same_candidate`、`test_trace_self_declaration_must_be_false_but_is_not_binary_inspection`、`test_mutation_11_hmac_rank_has_multiple_pair_sample_golden_order`、`test_live_site_must_equal_spec_site_before_output_reservation`、`test_mutation_06_live_env_mismatch_rejects_before_output_reservation`

## 未了・判断を仰ぐ点

pytest の実走確認のみ未了です。実装上の追加判断事項はありません。

## 総括

共有 fixture の changed-path を、呼び手が指定する実 spec relpath から生成するよう修正しました。  
issuer fixture は `refs/spec.json` を明示し、観測された10件の共通原因を解消しています。  
指定された2ファイル以外は編集しておらず、commit 操作もしていません。  
構文と差分形式は確認済みですが、Pegasus dispatch 障害のため pytest は未実走です。