静的再レビューの結論は、`closed` 10 件、`partial` 1 件、`regressed` 1 件です。R2 は `_CERTIFIED_RUNNER` / `_CERTIFIED_WHICH` により実質後退しています。pytest と変異試験は実走していません。

以下、`P` は [p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/campaign/p3_b4_closed_critic.py)、`T` は [test_p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1697-closed-critic/orchestrator/tests/test_p3_b4_closed_critic.py) です。

## R1〜R12 判定

|所見|判定|production 根拠|test nodeid / 判定理由|
|---|---|---|---|
|R1|closed|P:1105-1371 が terminal bytes、exact schema、start・payload・argv・envelope・各 hash を再検証。P:1374-1419 が path 入力、`pair_id` equality を要求。|`T::test_r1_terminal_pair_revalidation_rejects_status_and_payload_byte_tamper`、`::test_m17_pair_id_accepts_one_factory_and_rejects_mixed_factories_only`、`::test_m19_pair_gate_accepts_terminal_paths_and_rejects_promoted_dataclasses`|
|R2|regressed|P:84-85 の module 属性を P:907-1016 が certified trust root として直接使用。両属性の差替えだけで fake runner と任意 executable を certified 化できる。|`T::test_m5_certified_runner_identity_accepts_module_seam_and_rejects_other_runner` 自身が T:464-476 で両 seam を差し替えて certified pair を正例化。`_pair_fixture(certified=True)` も T:274-294 で同じ操作を行う。|
|R3|closed|P:702-717 は arm から `reflux=(arm == "on")` を導出して payload を生成。|`T::test_m16_sent_on_off_payload_bytes_match_independent_admitted_view_digests` が独立 digest と byte 比較し、on の marker 出現と off の不出現を固定。|
|R4|closed|P:747-768 が provider admission を経由し、P:802-809 と P:1312-1360 が envelope evidence と成功不変条件を再検証。|`T::test_r4_num_turns_gate_has_one_field_positive_negative_pair`、`::test_r4_permission_denials_gate_has_one_field_positive_negative_pair`、`::test_r4_server_tool_use_gate_has_one_field_positive_negative_pair`。各々 exact reason 付き。|
|R5|closed|P:726-746 が再検証可能 bytes を保存し、P:763-816 が hash を記録、P:1208-1304 が保存 bytes から再計算。|`T::test_p2_successful_test_only_invocation_records_snapshot_and_returns_data_only`、`::test_m16_sent_on_off_payload_bytes_match_independent_admitted_view_digests` が WAL、state、digest、payload、argv、start bytes と exact 比較。|
|R6|closed|P:751 は decision を data として parse、P:826-831 は invocation を返すだけで loop state/proposal へ fold しない。|`T::test_a8_parser_returns_reverse_boolean_as_data_without_state_or_proposal_fold` が実 loop-state bytes、campaign tree、artifact root を invoke 前後で検査。|
|R7|closed|P:1422-1455 が factory、両 invoke、pair gate、stdout、失敗 rc=1 を実装。|`T::test_r7_a10_thin_cli_drives_factory_both_arms_pair_gate_and_failure_rc`|
|R8|closed|P:504-540 に裁定指定の三依存を含む closure manifest と hash がある。|`T::test_m15_m20_projection_manifest_exactly_hashes_all_independent_sources` が test 側対応表から全 entry と contract bytes を独立再計算。|
|R9|closed|P:107-110、399-419 が引用 path 全体を処理し、JSON decode 後の残存 escape を再 decode しない。|`T::test_r9_json_decode_accepts_literal_escape_explanation_and_rejects_json_alias`、`::test_r9_quoted_space_path_accepts_policy_digest_and_rejects_normalized_alias`、`::test_m12_normalized_view_accepts_real_digest_and_rejects_parent_alias`|
|R10|partial|P:330-382 の現行 gate 自体は exact type/value を検査。|`T::test_r10_response_field_types_have_exact_one_field_positive_negative_pairs` と `::test_r10_payload_field_values_have_exact_one_field_positive_negative_pairs` は大半を固定するが、`projected_digest=1` の負例がない。|
|R11|closed|P:683-697 が query 前に terminal slot を予約し、start 書込みを try 内で実行。P:832-878 が同じ fd で failure terminal を確定。|`T::test_r11_terminal_slot_precedes_query_and_start_failure_gets_terminal_record` が query 時の空予約と start failure terminal を検査。|
|R12|closed|P:2-16 は route-local candidate へ縮小。P:112-132、219-224 に trust、capability、snapshot、storage の非保証を明記。|`T::test_a7_receipt_names_exact_literal_guarantee_and_indirect_non_guarantees`、`::test_p1_policy_admitted_synthetic_wal_digests_pass_payload_identity_gate`、`::test_m16_sent_on_off_payload_bytes_match_independent_admitted_view_digests`|

R1・R3・R5 の production gate と対応する byte-level test は 2 巡目でも緩んでいません。ただし、それらの certified 正例を作る入口自体は R2 の seam により弱体化しています。

## seam と共有 module patch の棚卸し

- `subprocess.run` の差替え: **0 箇所**。T:227 は参照保存、T:285 は identity 確認だけ。
- `shutil.which` の差替え: **0 箇所**。
- `unittest.mock.patch.object` の静的 call site: **7 箇所、distinct 属性 5 個**。すべて共有 module `C` の属性。
  - `C.exploration_campaign_layout`: 1 箇所、T:269
  - `C._CERTIFIED_WHICH`: 2 箇所、T:275、464
  - `C._CERTIFIED_RUNNER`: 2 箇所、T:280、466
  - `C._write_exclusive_json`: 1 箇所、T:1238
  - `C.assert_b4_arm_pair`: 1 箇所、T:1375

したがって、大域 `subprocess` / `shutil` patch は全廃されていますが、共有 module 属性の patch 自体は全廃されていません。特に certified seam 4 箇所は単なる test isolation ではなく、production が certified 判定に使う値を直接変更しています。

## 新たな所見

### 1. [must-fix] certified seam により R2 が regressed

- **(a) 何が壊れるか:** `_CERTIFIED_WHICH` と `_CERTIFIED_RUNNER` を差し替えるだけで、fake runner 由来 receipt が `evidence_class="certified"` になる。
- **(b) 根拠:** P:84-85、907-1016。実証する test 操作は T:274-294、460-476。
- **(c) 最小是正案:** certified production 経路から両 seam を外し、runner/executable 注入は `create_b4_closed_critic_pair_for_test` だけに限定する。fake runner を certified 正例に使わない。
- **(d) 成果物影響:** critic CLI を実行していない偽 block が certified 受理集合、材料レポート、試行台帳へ入る。

### 2. [must-fix] R10 の `projected_digest` 非 str 負例が欠落

- **(a) 何が壊れるか:** P:378 の type 条件だけを削る変異では、truthy な `projected_digest=1` が通るが現 test は赤くならない。
- **(b) 根拠:** production は P:374-382。test は T:679-699 で空 digest、未知 result、非 str result だけを試し、非 str digest を試していない。
- **(c) 最小是正案:** 同 node または隣接 node に `{"projected_digest": 1, "result": "rejected"}` の exact-reason 負例を1件追加する。
- **(d) 成果物影響:** type gate 退行時に malformed digest が成功 receipt へ束縛される。

## 改訂後の変異 15 件

以下は実走結果ではなく、現コードに対する静的 KILL 判定です。

|変異|静的判定|単一理由と検出 nodeid|
|---|---|---|
|M1|KILL、単一理由|campaign-id literal gate のみ。`T::test_m1_campaign_id_gate_accepts_real_digest_and_rejects_only_literal_injection`|
|M2|KILL、単一理由|repository-root literal gate のみ。`::test_m2_repository_root_gate_accepts_real_digest_and_rejects_only_literal_injection`|
|M3|KILL、単一理由|campaign-path literal gate のみ。`::test_m3_campaign_path_gate_accepts_real_digest_and_rejects_only_literal_injection`|
|M4|KILL、単一理由|module-derived root equality のみ。`::test_m4_module_root_control_accepts_exact_root_and_rejects_decoy_before_factory`|
|M5|KILL、単一理由|別 runner の identity rejection。`::test_m5_certified_runner_identity_accepts_module_seam_and_rejects_other_runner`。ただし seam 自体の差替えは正例化されており、R2 closure の証拠にはならない。|
|M10|KILL、単一理由|response の extra key gate。`::test_m10_p3_response_parser_accepts_exact_five_fields_and_rejects_extra_key`|
|M12|KILL、単一理由|normalized path view。`::test_m12_normalized_view_accepts_real_digest_and_rejects_parent_alias`|
|M13|KILL、単一理由|receipt の claim/evidence field 分離。`::test_m13_success_receipt_separates_claims_and_binds_raw_envelope_payload_argv`|
|M14|KILL、単一理由|success/failure terminal の実在と status。`::test_m14_success_and_failure_both_create_start_and_exclusive_terminal_receipts`|
|M15|KILL、単一理由|manifest 全 entry の exact 対応表比較。`::test_m15_m20_projection_manifest_exactly_hashes_all_independent_sources`|
|M16|KILL、単一理由|off payload が独立 `reflux=False` digest と不一致になり marker も混入。`::test_m16_sent_on_off_payload_bytes_match_independent_admitted_view_digests`|
|M17|KILL、単一理由|混成 pair が `pair_id` gate だけを失う。`::test_m17_pair_id_accepts_one_factory_and_rejects_mixed_factories_only`|
|M18|KILL、単一理由|caller decoy が argv/receipt executable へ現れる。`::test_m18_certified_fixed_claude_resolution_ignores_caller_executable_decoy`|
|M19|KILL、単一理由|昇格 dataclass が path-only gate を通る。`::test_m19_pair_gate_accepts_terminal_paths_and_rejects_promoted_dataclasses`|
|M20|KILL、単一理由|`artifact_admission` entry 欠落による manifest exact mismatch。`::test_m15_m20_projection_manifest_exactly_hashes_all_independent_sources`|

改訂後 15 変異に静的な mask は見当たりません。ただし M5 と M18 の KILL は、module seam 自体を差し替えて certified を名乗れる破れを検出していません。

## 総括

**残る must-fix はあります。** R2 の certified seam 後退と、R10 の `projected_digest` 非 str 負例欠落の 2 件です。

親報告の 262 passed / 6 skipped は未変異 baseline の実走結果として扱えますが、今回私は再実走しておらず、上記の変異 KILL は静的判定です。R1・R3・R5と改訂15変異の単一理由性は維持されていますが、R2 regression が certified 入口そのものを弱めるため、現物を root cause closed とは判定しません。