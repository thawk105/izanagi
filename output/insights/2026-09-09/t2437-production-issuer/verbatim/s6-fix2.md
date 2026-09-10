## R1 の対応

**closed**

- Public issuer は hash 値ではなく、解決済みの exact `ExecutionEnvironmentContract` を必須入力として受け取ります。[reflux_result_evidence.py:1196](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix2/orchestrator/campaign/reflux_result_evidence.py:1196)
- 契約 hash と capability の一致、context の `env_tag` / `attestation_mode` と契約の一致、required 時の `verified_calibration` 存在を write 前に検査します。[reflux_result_evidence.py:1223](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix2/orchestrator/campaign/reflux_result_evidence.py:1223)
- `receipt_matches_contract()` への mode、tag、hash は契約実体から渡すため、context の自己申告だけでは検証分岐を選べません。[reflux_result_evidence.py:1245](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix2/orchestrator/campaign/reflux_result_evidence.py:1245)
- `loop.py` は `_authorize_measurement()` が返した `authorized_contract` 自体を issuer へ渡します。[loop.py:309](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix2/orchestrator/campaign/loop.py:309)、[loop.py:674](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix2/orchestrator/campaign/loop.py:674)、[loop.py:815](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix2/orchestrator/campaign/loop.py:815)

追加した負例はいずれも発行前後の file snapshot が完全一致します。

- required 契約 + v1 receipt: [test_reflux_result_evidence.py:1253](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix2/orchestrator/tests/test_reflux_result_evidence.py:1253)
- capability と hash が異なる契約実体: [test_reflux_result_evidence.py:1287](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix2/orchestrator/tests/test_reflux_result_evidence.py:1287)
- required 契約 + `verified_calibration=None`: [test_reflux_result_evidence.py:1322](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix2/orchestrator/tests/test_reflux_result_evidence.py:1322)

## R2 の 4 node

- N1: `orchestrator/tests/test_pipeline_verify_result_retention.py::test_admitted_remote_fanout_abort_has_no_typed_verify_result_before_projection`
  - `_admit_verify_fanout_result()` の戻り値を直接検査し、projection 前に `verify_result is None` を固定します。[test_pipeline_verify_result_retention.py:146](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix2/orchestrator/tests/test_pipeline_verify_result_retention.py:146)

- N2: `orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_refuses_wrong_expected_record_path_before_writes`
  - 不正な `expected_record_path` が `ResultEvidenceError` となり、file snapshot が変化しないことを固定します。[test_reflux_result_evidence.py:1487](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix2/orchestrator/tests/test_reflux_result_evidence.py:1487)

- N3: `orchestrator/tests/test_reflux_campaign_issuer.py::test_validate_result_evidence_context_rejects_multiple_genomes`
  - `_validate_result_evidence_context()` を直接呼び、multiple-genome predicate 単独の拒否を検査します。[test_reflux_campaign_issuer.py:867](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix2/orchestrator/tests/test_reflux_campaign_issuer.py:867)

- N4: `orchestrator/tests/test_reflux_campaign_issuer.py::test_validate_result_evidence_context_rejects_balanced_schedule`
  - 同 helper を直接呼び、1 genome のまま balanced predicate 単独の拒否を検査します。[test_reflux_campaign_issuer.py:885](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix2/orchestrator/tests/test_reflux_campaign_issuer.py:885)

## 実走した検査

Python 内から `pytest.main()` を呼ぶ自走 harness を使用しました。

- 新規 7 node: **7 passed in 3.53s**
- 指定 3 file 全 node: **103 collected / 95 passed / 8 failed / 0 skipped**
  - `test_reflux_result_evidence.py`: 全 82 node PASS
  - `test_pipeline_verify_result_retention.py`: 全 6 node PASS
  - `test_reflux_campaign_issuer.py`: 全 15 node中 7 PASS、8 件は既知の `contract-loader-drift`
- required 契約 + valid v2 receipt の直接正例も実走し、発行、resolver 解決、provenance の契約 hash 一致まで成功しました。

8 failure はすべて未 commit の `loop.py` と HEAD blob の不一致による `ident.py:287 IdentityMismatch` です。実装回帰による failure は観測していません。

`git diff --check`、所有 6 file の構文 compile、結合文字検査も成功しました。

## 現行の受理・拒否挙動

fix 前:

- capability と同じ hash を持つ required 契約由来の v1 receipt が、`context.attestation_mode="none"` により受理可能でした。
- issuer は契約実体を受け取らず、caller 提示の hash、tag、mode で認証分岐を決めていました。
- required 契約に対応する calibration が欠けても、自己申告 mode を none にすれば回避可能でした。

fix 後:

- capability に束縛された契約実体だけを受理します。
- context の tag/mode が契約と異なれば拒否します。
- required + v1、required + calibration 欠落、capability と契約 hash 不一致は、すべて新規 file 0 件で拒否します。
- required + valid calibration + valid v2 receipt は引き続き発行・解決できます。
- originless の分岐、record schema、provenance schema、既存テスト期待値は変更していません。

## 所有外 caller・共有 fixture・consumer test への波及

静的検索結果:

- `ResultEvidenceIssuanceContext` constructor の所有外 caller: 0
- `issue_campaign_result_evidence()` の所有外 caller: 0
- `_issue_campaign_result_evidence()` の所有外 caller: 0
- `run_campaign()` の公開 signature: 変更なし
- record / execution-provenance schema: 変更なし
- `pipeline.py`: 編集なし

読み取り専用で利用した共有 fixture:

- `orchestrator/tests/test_campaign.py`
- `orchestrator/tests/test_verify_fanout.py`
- `orchestrator/tests/reflux_origin_fixture_builder.py`

これら、および formal consumer test は編集していません。M12 の originless consumer 候補 3 nodeは今回未実走ですが、normal-result guard 自体は維持されています。

## 受入所要台帳へ登録すべき nodeid と実測所要

setup / call / teardown 合計秒です。`DRIFT` の秒数は既知 precondition failure までの時間であり、commit 後の成功所要としては再測定が必要です。

```text
PASS  0.019539  orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_terminal_mismatch[wrong-reason]
PASS  0.001698  orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_terminal_mismatch[wrong-verify-configs]
PASS  0.001535  orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_nonexact_accepted_verifier_order[empty]
PASS  0.001504  orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_nonexact_accepted_verifier_order[prefix]
PASS  0.001523  orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_nonexact_accepted_verifier_order[reverse]
PASS  0.001527  orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_nonexact_accepted_verifier_order[duplicate]
PASS  0.021076  orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonexact_typed_values[stats-bool]
PASS  0.020948  orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonexact_typed_values[cycle-bool]
PASS  0.020679  orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonexact_typed_values[reason-version-float]
PASS  0.019325  orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonproduction_witness_shape[unknown-phenomenon]
PASS  0.020074  orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonproduction_witness_shape[ring-mismatch]
PASS  0.019110  orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonproduction_witness_shape[unknown-reason-type]
PASS  0.018502  orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_shared_witness_digest_matches_independent_bytes
PASS  0.001957  orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_assembler_rejects_invalid_input
PASS  0.023782  orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_assembler_rejects_different_projection_same_attempt
PASS  0.002688  orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_issuer_resolves_before_record_creation
PASS  0.089011  orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_issuer_writes_nine_keys_create_only
PASS  0.345270  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_issues_real_wal_projection_and_resolves_interval
PASS  0.563643  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_preserves_nonzero_offset_for_second_attempt
PASS  0.202439  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_refuses_absent_execution_receipt_before_writes
PASS  0.166941  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_refuses_unauthenticated_receipt_before_writes[schema]
PASS  0.186415  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_refuses_unauthenticated_receipt_before_writes[env_tag]
PASS  0.225735  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_refuses_unauthenticated_receipt_before_writes[attestation_mode]
PASS  0.262060  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_refuses_interleaved_attempt_before_writes
PASS  0.378597  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_refuses_nonexact_verify_result_before_writes
PASS  0.359664  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_treats_create_only_collision_as_failure
PASS  0.386841  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_snapshot_survives_append_while_live_ref_breaks
PASS  0.217809  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_refuses_wrong_expected_record_path_before_writes
PASS  0.147621  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_refuses_required_contract_v1_receipt_before_writes
PASS  0.208736  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_refuses_contract_not_bound_by_capability_before_writes
PASS  0.175325  orchestrator/tests/test_reflux_result_evidence.py::test_campaign_producer_refuses_required_contract_without_verified_calibration
PASS  0.323945  orchestrator/tests/test_pipeline_verify_result_retention.py::test_local_rejected_repetition_retains_exact_verify_result_and_wal_binding
PASS  0.451877  orchestrator/tests/test_pipeline_verify_result_retention.py::test_remote_fanout_abort_does_not_reconstruct_typed_verify_result
PASS  0.434096  orchestrator/tests/test_pipeline_verify_result_retention.py::test_abort_rejects_non_exact_verify_result
PASS  0.893074  orchestrator/tests/test_pipeline_verify_result_retention.py::test_accepted_evaluation_does_not_retain_one_pass_verify_result
PASS  0.274985  orchestrator/tests/test_pipeline_verify_result_retention.py::test_prebuild_abort_retains_generated_build_attempt_id
PASS  0.251239  orchestrator/tests/test_pipeline_verify_result_retention.py::test_admitted_remote_fanout_abort_has_no_typed_verify_result_before_projection
DRIFT 0.333792 orchestrator/tests/test_reflux_campaign_issuer.py::test_real_run_campaign_issues_rejected_record_and_originless_is_inert
DRIFT 0.149562 orchestrator/tests/test_reflux_campaign_issuer.py::test_originless_campaign_has_legacy_literal_artifact_and_wal_shape
PASS  0.002608  orchestrator/tests/test_reflux_campaign_issuer.py::test_originless_campaign_does_not_evaluate_issuer_only_attributes
PASS  0.003008  orchestrator/tests/test_reflux_campaign_issuer.py::test_context_shape_rejects_multiple_genomes_and_balanced_before_writes
PASS  0.003716  orchestrator/tests/test_reflux_campaign_issuer.py::test_context_exact_type_and_root_binding_precede_campaign_writes
DRIFT 0.145280 orchestrator/tests/test_reflux_campaign_issuer.py::test_accepted_terminal_recovery_is_refused_without_new_evidence[False]
DRIFT 0.183083 orchestrator/tests/test_reflux_campaign_issuer.py::test_accepted_terminal_recovery_is_refused_without_new_evidence[True]
DRIFT 0.177779 orchestrator/tests/test_reflux_campaign_issuer.py::test_identity_error_terminal_is_explicitly_refused
DRIFT 0.156521 orchestrator/tests/test_reflux_campaign_issuer.py::test_originless_eval_exception_after_terminal_preserves_legacy_abort
DRIFT 0.258942 orchestrator/tests/test_reflux_campaign_issuer.py::test_context_eval_exception_is_refused_without_result_evidence[False]
DRIFT 0.286442 orchestrator/tests/test_reflux_campaign_issuer.py::test_context_eval_exception_is_refused_without_result_evidence[True]
PASS  0.003233  orchestrator/tests/test_reflux_campaign_issuer.py::test_issuance_rejects_invalid_origin_capability_campaign_id
PASS  0.000812  orchestrator/tests/test_reflux_campaign_issuer.py::test_signature_keeps_context_keyword_only_after_verify_fanout_hosts
PASS  0.002702  orchestrator/tests/test_reflux_campaign_issuer.py::test_validate_result_evidence_context_rejects_multiple_genomes
PASS  0.002684  orchestrator/tests/test_reflux_campaign_issuer.py::test_validate_result_evidence_context_rejects_balanced_schedule
```

## 契約の問題

無し。

## 総括

R1 は閉塞し、R2 の N1〜N4 はすべて追加・単独実走済みです。既存期待値の変更、所有外編集、docs 編集、commit、push、ブランチ操作はありません。変更は所有内 5 file のみで、`pipeline.py` は編集不要でした。