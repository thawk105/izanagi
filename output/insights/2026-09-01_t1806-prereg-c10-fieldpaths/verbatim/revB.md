## 所見

[severity: must-fix] [事前登録された M01-COND survivor が実装されていない] 新設テストの parameter は `unexpected-extra-field-path`、`binding-pair-removed`、`verifier-literal-removed` の3件で、すべて最終的に `UNSATISFIED` を要求している。baseline の token-only fixture は値照合を最初から持たず、指定された「`proposal_build_source_bindings` の literal を残して、その field の照合だけを恒真化する」条件版変異ではない。このため M01-UNCOND と M01-COND の対が機械的に登録されていない。成果物影響: 現時点の certified 選択・受理集合は変わらないが、C10 が値束縛の弱体化を検出しないという限界を proof chain の変異証拠として示せず、gate の検出力を過大に記録し得る。[根拠 s4-adjudication.md:107; orchestrator/tests/test_s8c_preregistration_predicates.py:2818] [提案: active な `proposal_build_source_bindings` 値照合を持つ source と、その照合だけを恒真化した source を対にし、後者でも C10 が `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` のままになる専用 survivor test を追加する。producer functional test は同じ変異を拒否することを別に確認する]

[severity: nit] [改名した v6 node が duration ledger に残る] production pin は v7へ閉じている一方、実測 duration ledger には旧 `test_decider_version_binds_cross_module_semantics_to_v6` key が残り、v7 node と新規3 parameter は未収録である。これは意味論 pin ではなく実行順序のヒューリスティックなので、手計算値での更新は不要である。成果物影響: certified 選択・受理集合・proof chain は変わらず、焦点走の scheduling 推定だけが既定値へ落ちる。[根拠 orchestrator/tests/acceptance_duration_ledger.json:13812; orchestrator/tests/test_s8c_preregistration_core.py:2403] [提案: clean 木で実測可能になった時点の ledger 再生成で追随し、それまでは coverage meta test を焦点走へ含める]

## 実装子の報告と差分の食い違い

[severity: nit] [報告後に親の g12 発行と commit が完了している] 実装報告は「5 file modified・g12未発行・未commit」だが、現在は worktree が clean で、HEAD `9feff6b07` に6ファイル目の `condition-freeze.v1.g12.json` を含む変更が commit 済みである。これは想定された親の後続処理と整合し、未知の編集ではない。成果物影響: 現在の proof chain は報告時点より進み、新契約 hash と v7 を g12 に束縛済みである。[根拠 s5/impl.md:60; s5/impl.md:71; output/s8c-preregistration/condition-freeze/condition-freeze.v1.g12.json:1] [提案: 以後の検査・報告は `cb4a11b6e..9feff6b07` の6ファイルを対象とする]

上記時系列差と M01-COND 以外では、報告した5ファイルの変更はすべて差分に存在し、報告外の実装変更は g12 のみだった。

## 焦点走に含めるべき test node の列挙

hash・版・発行 guard:

```text
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_accepts_non_path_controls[nul]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_accepts_non_path_controls[cr]
orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_accepts_non_path_controls[lf]
orchestrator/tests/test_s8c_preregistration_core.py::test_current_evidence_contract_hash_is_frozen
orchestrator/tests/test_s8c_preregistration_core.py::test_matching_decider_version_preserves_activation_conjunction
orchestrator/tests/test_s8c_preregistration_core.py::test_decider_version_binds_cross_module_semantics_to_v7
orchestrator/tests/test_s8c_preregistration_core.py::test_invalid_running_decider_version_cannot_activate
orchestrator/tests/test_s8c_preregistration_core.py::test_valid_hostile_str_subclass_cannot_fake_decider_version_match
orchestrator/tests/test_s8c_preregistration_core.py::test_generation_added_without_protected_change_is_spurious
orchestrator/tests/test_s8c_preregistration_core.py::test_prepare_revision_is_exclusive_create
```

C10 evaluatorと実 repository snapshot:

```text
orchestrator/tests/test_s8c_preregistration_predicates.py::test_c10_load_bearing_check_proves_literal_presence_only_not_field_generation_reread_or_value_binding[unexpected-extra-field-path]
orchestrator/tests/test_s8c_preregistration_predicates.py::test_c10_load_bearing_check_proves_literal_presence_only_not_field_generation_reread_or_value_binding[binding-pair-removed]
orchestrator/tests/test_s8c_preregistration_predicates.py::test_c10_load_bearing_check_proves_literal_presence_only_not_field_generation_reread_or_value_binding[verifier-literal-removed]
orchestrator/tests/test_s8c_preregistration_predicates.py::test_noop_and_token_only_fixtures_never_satisfy[nc_c10_raw_response_unbound-C10]
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_snapshot_has_zero_satisfied_predicates
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_snapshot_exactly_matches_head
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_gap_reason_snapshot_requires_cross_wave_review
```

producer consumer。13 field parameter は省略せず全件対象にすべきで、特に最後の専用分岐は必須:

```text
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_positive_binds_all_fields
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_no_build_is_explicitly_unbound
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation[input_payload_sha256]
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation[raw_response_path]
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation[raw_response_sha256]
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation[provider_payload_sha256]
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation[provider_envelope_sha256]
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation[proposal_path]
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation[proposal_sha256]
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation[build_records]
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation[bench_records]
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation[artifact_refs]
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation[source_refs]
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation[admission_decision]
orchestrator/tests/test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation[proposal_build_source_bindings]
```

g12・candidate 閉包:

```text
orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain
orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_batch_is_bounded_by_frozen_touch_points
orchestrator/tests/test_s8c_preregistration_invariant.py::test_repository_tip_binds_current_decider_version_without_activation
orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_is_not_effective_and_has_zero_satisfied_predicates
orchestrator/tests/test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan
```

collection meta:

```text
orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection
orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes
```

新規 test file はなく、既存 predicate file に3 instanceを追加した形である。ただし collection 数と ledger join は変わるため、上記 meta test は対象に残すべきである。

## 総括

must-fix は1件、M01-COND の明示的 survivor test 欠落である。それ以外の静的照合結果は次のとおり。

- canonical JSON + `izanagi:s8c:evidence-contract:v1\0` から独立再計算した契約 hashは `26f7bd4776bff58753f7f1dc7ebecdc5a3d3f1e0f108e1fbc541fdd33dbc13e5`。生 bytes hash `e1f739…03a7` とは区別できている。
- 派生 pin 3値も `323840…4cdf`、`23d203…83e6`、`c9885e…bf90` で差分と一致。
- 13組の対応表は literal/path とも13 unique、契約13 pathと完全一致し、production verifier ASTに13 literalが存在する。
- g11 raw hash `8fb780…a307` は g12 `supersedes_sha256` と一致。g12 protected hashも独立再計算した `ac26b8…8245` と一致し、g11 protectedとは異なるため、発行前状態では `spurious-revision` にならない。
- g12は canonical JSONで、§5・§6・normative hashはg11から不変。契約JSONの挿入位置・インデントも既存規則と一致。
- 禁止対象の `docs/`、g10/g11、`autonomous_trial_completeness.py`、`campaign_lock.py`、`test_s8c_gate_report.py` は未変更。`output/` の変更は必要なg12だけ。
- 新設テストに commit 前後で変わる HEAD hashの期待値はない。
- pytest は実走していないため、いずれの node も「緑」とは判定していない。