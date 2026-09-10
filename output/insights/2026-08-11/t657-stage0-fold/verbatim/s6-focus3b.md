判定は **NO-GO**。現行 helper 自体に可視部と検査対象を再分離する実装欠陥は見つかりませんでしたが、変異台帳の node 帰属と検証網羅性が段 6 契約を満たしていません。

### S6F-01

- **主張:** M1 の 2 node、M7 の 31 node は、受理集合が変わらず拒否理由だけが変わった赤である。7 mutant は別の真の node により全件 KILLED のままだが、`failed_nodes` をすべて検出力証拠として扱えない。
- **file:line 根拠:** M1 の登録・実測集合は [mutation-ledger.json:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/mutation-ledger.json:55)、M7 は [mutation-ledger.json:366](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/mutation-ledger.json:366)。各陰性 node は拒否理由 substring の違いでも赤になる [test_calibration_freeze_authority_contract.py:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:124)。M7 は全検証に先行する schema 比較で落ちる [calibration_freeze_authority_contract.py:794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:794)。
- **具体的な不具合シナリオ:** M1 で opener 検出を外すと fenced-decoy と tab-decoy は canonical/relaxed 表の重複で引き続き拒否され、診断だけが変わる。M7 では `return ()` が本来別理由で拒否される31負例をすべて §7.5 schema drift へ先行拒否する。
- **深刻度:** **must-fix**
- **成果物影響:** mutation ledger の exact failed-node attribution が DW-M03/M08 に違反する。ただし真の KILL は M1=8 node、M7=6 node、M2〜M6=各登録 node に残るため、mutant 単位の 7/7 KILLED は維持される。

### S6F-02

- **主張:** `_match_fence_line` の現実装は列挙された top-level CommonMark 条件を満たすが、テストは helper の全選言を独立に殺せない。特に closer 側 `invalid_indent` は opener 側と同一 node に混在し、単独では未検証である。
- **file:line 根拠:** opener/closer の共通判定は [calibration_freeze_authority_contract.py:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:348)、closer の `invalid_indent` 分岐は [calibration_freeze_authority_contract.py:415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:415)。唯一の tab node は invalid opener と invalid closer を同居させる [test_calibration_freeze_authority_contract.py:999](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:999)。closer 後続非空白、space+tab の途中 tab stop、CRLF、行末空白、2-marker ordinary line の独立 node もない。
- **具体的な不具合シナリオ:** 将来 closer の「後続は空白だけ」判定を削除して `````spoof`` を closer と誤認する回帰や、closer 側だけ tab を1列として扱う回帰が入っても、現行70 nodeとM1〜M7はその選言を単独では殺さない。
- **深刻度:** **must-fix**
- **成果物影響:** 現行 bytes は正しいが、4巡目で意図した「helper 条件全体の回帰防壁」は未完成である。

### S6F-03

- **主張:** 2つの独立 hash pin に、それぞれを単独で到達・殺す陰性 node がない。
- **file:line 根拠:** fixture entry 列の独立 pin は [calibration_freeze_authority_contract.py:1087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:1087)、row ID 集合 pin は [calibration_freeze_authority_contract.py:1121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:1121)。既存 fixture hash node は自己整合だけを変える [test_calibration_freeze_authority_contract.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:742)。required-gates pin には対照的に単独 reorder node がある [test_calibration_freeze_authority_contract.py:721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:721)。
- **具体的な不具合シナリオ:** `_EXPECTED_FIXTURE_ENTRIES_SHA256` 比較または `_EXPECTED_ROW_IDS_SHA256` 比較だけを無効化しても、現行 fixture は canonical 値のままなので既存負例は前段で落ち、該当 pin の欠落を示す node が赤にならない。後者が他の raw pin と冗長なら、その事実を明記して単独変異証拠から外す必要がある。
- **深刻度:** **must-fix**
- **成果物影響:** 「manifest literal・実体・独立期待値の三者比較」という §10 の保証の一部が、静的読解だけに依存している。

確認結果は以下です。

- `_match_fence_line`: space/tab 混在を tab stop 4 で数え、3列以下のみ fence、marker は3個以上、backtick info 内の backtick は拒否、tilde info は許可、closer は同種・opener以上・後続space/tabのみ。CRLF除去、長いcloser、異種/短いcloser、fence内markerも実装上正しい。
- `invalid_indent`: opener は可視行へ残して最終拒否、closer は fence を閉じず最終拒否へ繋がる。closer側で真になる入力は `\t``` ` 等であり、現在の tab node 内でも到達するが opener 側の拒否にmaskされる。`offset > 3` は「旧 `[ \t]{0,3}` でも受理しなかった行」を通常本文として扱う条件である。
- 未閉鎖 fence はCommonMarkより厳しく文書全体を拒否する。invalid backtick-info ordinary text の拒否と同じく fail-closed な受理集合縮小であり、可視側だけを緩和する経路ではない。
- 段0の現行bytes直接算出は `required_gates=13`、`blocking=5`、`status=incomplete`、`pending=5`、`applicable_unresolved=2`。算出経路は [calibration_freeze_authority_contract.py:1131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:1131)。
- §7.5 は専用recordの有無自体を未裁定とする [bundle-design.md:504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:504)。§12.3も(a)/(b)/(c)を候補、(a)を推奨、gateを`unresolved`と明記する [bundle-design.md:865](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:865)。決定済み表現はない。
- `fe43b92b` が取り込んだ側はmerge-baseから52 commit。対象3ファイル、execution helper/test、fixture treeへのmain側差分は0で、直接production依存にも重複変更はない。提示済みmain後70 passedとも整合し、干渉は認めない。
- 発火しないassert、hash自己参照、`_read_design` consumer取り残し、事後に合わせた期待値は確認しなかった。段6 execution-boundary第3選言には現在、単独陰性 node がある [test_calibration_freeze_authority_contract.py:1118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:1118)。

## 総括

- 判定: **NO-GO**
- blocker の所見 ID: **なし**
- FOCUS6R2-01: **closed** — helper は文字数でなくtab stop 4のcolumnで判定し、旧scannerだけが認識するindentをfail-closed拒否する。ただし独立回帰nodeの不足はS6F-02
- FOCUS6R2-02: **closed** — invalid-info fixtureはcanonical表だけを残し、M1では拒否理由変更でなく実受理へ倒れる
- FOCUS6R2-04: **closed** — §7.5と§12.3の双方が専用cancellation recordの有無を未裁定と明記する
- 変異台帳に「拒否理由の文字列だけの赤」が混ざっているか: **混入あり** — M1: `test_design_fenced_decoy_is_not_authoritative`, `test_design_tab_indented_fence_decoy_is_rejected`; M7: `test_current_repository_is_rejected_as_stage0_incomplete`, `test_orphan_case_file_is_rejected`, `test_declared_design_row_removed_is_rejected`, `test_manifest_raw_sha256_literal_tamper_is_rejected`, `test_design_stage6_live_tip_relaxation_is_rejected`, `test_false_pending_count_is_rejected`, `test_rejected_post_activation_lease_is_rejected`, `test_design_stage6_row_only_in_long_backtick_fence_is_rejected`, `test_pending_binding_with_positive_control_is_rejected`, `test_executable_binding_without_positive_control_is_rejected`, `test_case_file_bytes_tamper_with_manifest_unchanged_is_rejected`, `test_adjudicated_xf_position_cannot_regress_to_unresolved`, `test_design_stage6_contradictory_control_suffix_is_rejected`, `test_deferred_seal_ruling_cannot_be_resolved`, `test_design_stage6_execution_boundary_tail_drift_is_rejected`, `test_case_and_manifest_hash_tamper_together_is_rejected`, `test_adjudicated_revocation_cannot_regress_to_unresolved`, `test_manifest_entry_without_case_file_is_rejected`, `test_ruling_profile_order_drift_is_rejected`, `test_s2_profile_without_not_applicable_guarantee_is_rejected`, `test_adjudicated_u_a1_cannot_regress_to_unresolved`, `test_design_stage6_row_only_in_tilde_fence_is_rejected`, `test_design_row_removed_is_rejected`, `test_adjudicated_rollback_cannot_regress_to_unresolved`, `test_manifest_status_cannot_claim_complete_while_gates_remain`, `test_design_stage6_policy_gate_id_drift_is_rejected`, `test_not_applicable_outside_applicability_rule_is_rejected`, `test_resolved_ruling_without_design_selection_enum_is_rejected`, `test_unknown_case_key_is_rejected`, `test_placeholder_string_is_rejected`, `test_design_stage_scope_matches_fixture_assignment_gate_id`