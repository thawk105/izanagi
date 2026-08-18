## 総括

段 6 の blocker / must-fix を修正しました。docs 編集、commit、`git add`、branch 操作はしていません。

- 1: 修正済み。検証済み WAL bytes から直接 record を構成し、artifact / loop state も検証済み bytes を使用。admission 再読後の lock / WAL digest も再照合。
- 2: 修正済み。Layer 3 と同じ `trigger_binding` 正規化を C10 に適用し、fixture は実 trigger binding 付きへ変更。
- 3: 修正済み。`bench_wall_s` 欠落は 0.0 補完せず拒否。
- 4: 修正済み。campaignless failure cell が C09/C10 へ到達し、非認証受理と reason code 積載が可能。
- 5: 修正済み。`schema_version` 欠落は `AcceptanceReceiptError` で拒否。
- 6: 修正済み。`layer3-chain-absent` を逐語で pin。
- 7: 修正済み。M01-M11 の負例を追加または修正。
- 8: 修正済み。6 report acceptance は workload 未実装による exact fail-closed を pin。C10 単体の実 build 正例は trigger binding 付きで維持。

追加・改名テスト:

- `test_s8c_acceptance_registered_build_reports_are_unreachable_until_workload_definition`: exact workload reason と receipt 未生成を確認。
- `test_s8c_acceptance_no_build_verifier_leaf_is_independently_recomputed`: no-build leaf の呼出しと独立再計算を確認。
- `test_s8c_acceptance_build_with_empty_cells_fails_closed_before_receipt`: 空 cells 拒否。
- `test_s8c_acceptance_failure_cell_pins_layer3_chain_absent_reason`: failure reason の逐語確認。
- `test_s8c_acceptance_rejects_campaign_from_different_output_root`: output root 不一致拒否。
- `test_verify_s8c_cross_binding_projects_from_verified_wal_bytes`: 検証済み WAL bytes の使用を確認。
- `test_verify_s8c_cross_binding_rejects_missing_bench_wall_s`: 欠落 bench 値拒否。
- `test_verify_s8c_cross_binding_rejects_an_unclassified_wal_record`: 未分類 WAL 追加拒否。
- `test_missing_schema_version_is_acceptance_receipt_error`: v1/v2/v3 の schema 欠落拒否。

M01-M11 の kill 対応:

- M01: `test_s8c_acceptance_registered_build_reports_are_unreachable_until_workload_definition`
- M02: `test_s8c_acceptance_build_with_empty_cells_fails_closed_before_receipt`
- M03: `test_p5_six_complete_terminal_reports_pass_acceptance`
- M04: `test_s8c_acceptance_failure_cell_pins_layer3_chain_absent_reason`
- M05: `test_s8c_acceptance_no_build_verifier_leaf_is_independently_recomputed`
- M06: `test_s8c_acceptance_rejects_campaign_from_different_output_root`
- M07: `test_read_and_verify_bytes_rejects_changed_bytes`
- M08: `test_verify_s8c_cross_binding_rejects_each_reference_mutation[raw_response_sha256]`
- M09: `test_verify_s8c_cross_binding_rejects_an_unclassified_wal_record`
- M10: `test_verify_s8c_cross_binding_rejects_each_reference_mutation[artifact_refs]`
- M11: `test_v3_aggregate_is_recomputed_from_trial_leaves`

変更前は、failure cell が前段で拒否され、WAL 再読や欠落値補完、schema 欠落の raw `KeyError` が発生し得ました。  
変更後は、検証済み bytes に束縛して fail-closed に判定し、failure reason と例外契約を保持します。

`check_codex_agents.py`、`check_docs.py`、AST 検査、`git diff --check` は成功しました。pytest は親の実測範囲のため、実装済み・未実走です。