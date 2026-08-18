## 総括

実装済み・未実走。commit、`git add`、branch 操作は未実施。`git diff --check` は通過し、docs・契約 JSON・評価器・凍結出力・producer は変更していません。

前子の差分は、受領証 v3、acceptance の C09/C10 配線、12 field 負例、6 report build fixture、v3→v1 projection、machine-contract pin を採用しました。修正したのは次の点です。

- `verify_s8c_cross_binding` 本体で、`input_payload_sha256`、`raw_response_path`、`raw_response_sha256`、`provider_payload_sha256`、`provider_envelope_sha256` を再読・sha256照合。
- C10 fixture を trigger-binding なしの WAL にして Layer 3 投影と整合。
- build fixture の genome を canonical な `fixture|` に統一し、variant も再計算。
- v3→v1 projection の未定義 `canonical` を修正。

変更 file は次の9件です。

- [autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/autonomous_trial_completeness.py)
- [trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/trial_registry.py)
- [s8c_acceptance_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/s8c_acceptance_receipt.py)
- 対応する4つのテスト file、reflux compatibility、receipt v2、preregistration invariant/predicate。

追加・改名テスト:

- `test_read_and_verify_bytes_rejects_changed_bytes`: 正常 byte を受理し、変更後を拒否。
- `test_verify_s8c_cross_binding_positive_binds_all_fields`: 12 field の正例。
- `test_verify_s8c_cross_binding_no_build_is_explicitly_unbound`: no-build の12 field未束縛を確認。
- `test_verify_s8c_cross_binding_rejects_each_reference_mutation`: `input_payload_sha256`、`raw_response_path`、`raw_response_sha256`、`provider_payload_sha256`、`provider_envelope_sha256`、`proposal_path`、`proposal_sha256`、`build_records`、`bench_records`、`artifact_refs`、`source_refs`、`admission_decision` の各変異を拒否。
- `test_s8c_acceptance_build_runs_layer3_and_cross_binding_for_six_reports`: Layer 3 と C10 を通る6 report 正例。
- `test_v3_requires_cross_binding_receipt_sha256`、`test_v3_aggregate_is_recomputed_from_trial_leaves`: v3 必須値と改竄拒否。
- `test_acceptance_v2_has_no_certifying_issuance_branch` を `test_acceptance_v3_has_no_certifying_issuance_branch` に改名。
- `_project_t822_receipt_v2_to_v1` を `_project_t822_receipt_v3_to_v1` に改名。

meta-test の pin は、`test_verify_s8c_cross_binding_positive_binds_all_fields`、`test_verify_s8c_cross_binding_no_build_is_explicitly_unbound`、`@pytest.mark.parametrize("mutation", C.S8C_CROSS_BINDING_FIELDS)`、`test_machine_contract_function_names_exist_and_checked_set_is_exact`、`test_current_repository_gap_reason_snapshot_requires_cross_wave_review` です。改名した acceptance test 名を文字列で固定する別 meta-test は見つかりませんでした。

静的な波及先は、acceptance CLI の `trial_registry.py`、`test_trial_registry.py`、originless compatibility の acceptance builder、`verify_autonomous_trial_files` の呼出元、receipt v1/v2/v3 の parser/consumer tests、Layer 3 の legacy receipt fixtureです。既存の未追跡 `output/insights/2026-08-18_t1348-c09-c10-consumer/` は触れていません。

変更前は build acceptance が Layer 3/C10 を独立検証せず v2 receipt を発行していました。変更後は `accepted.append` 前に root、Layer 3 chain、全 byte binding を検証し、v3 receipt の leaf と aggregate を発行します。

pytest はユーザー指示に従い実行していません。親が報告した snapshot nodeid `orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_gap_reason_snapshot_requires_cross_wave_review` は、commit 済み HEAD を対象にするため、親の commit 前は既知の赤として残しています。