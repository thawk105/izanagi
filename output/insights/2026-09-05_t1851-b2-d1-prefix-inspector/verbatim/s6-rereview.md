| 所見 | 判定 | 静的再レビュー結果 |
|---|---|---|
| F1 | **closed** | [実測] [実台帳 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:1118) は、同じ shared root に production API で v2 世代 A/B を作成する。reported artifact/proof は B、wrapper 外部引数は A。正常実装は A の台帳で B head を拒否し、A/A は受理する。real inspector は monkeypatch していない。 |
| F2 | **closed** | [実測] 通常 v5 helper から手書き validator と `raising=False` は消えた。[spy test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:663) は production validator を包み、reported/expected の2回を identity 付きで確認し、bool N、zero head、wrong schema も同じ node で拒否する。fake inspector test は外部 freeze/protocol/schedule から期待 binding を作り、拒否と受理の両方を持つ。 |
| F3 | **closed** | [実測] `test_floor_campaign_directly_reexports_shared_leaf_objects` は `git show 50dbf9158:...` の関数 bytes と完全一致した。移動分は [新規 node](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_contract.py:187) にある。 |
| F4 | **closed** | [実測] [M10 node](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:3455) は production scheduler authority で v1 を作り、`_profile_and_binding_for_generation` と `core.load_attempt_registry` の成功を直接 assert した後、v2-only guard の拒否を確認する。guard を v1/v2 許容へ変えれば他層に遮られず受理される。 |
| F5 | **closed** | [実測] [v4 node](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:819) は `None` を有効 proof にする局所 validator seam を持ち、正常時は validator 非呼出しと `[]` を確認する。[別 v5 node](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:871) が seam から inspector までの到達性を固定する。 |
| F6 | **closed** | [実測] genesis binding node と freeze/protocol proof mismatch node は、診断 node、reason 順序 pin、変異観測外と docstring に明記された。 |
| F7 | **closed** | [実測] [parametrize IDs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2496) は literal、digest 4種、row_count を区別する。 |

## 新規所見

blocker はありません。

### 所見 1 — fix1 証拠 patch と最終 tree が一致しない（must-fix）

(a) [実測] `s6-fix1.patch` は stats test を net `+206` とするが、最終 tree の段5との差は net `+248` で、42行多い。保存 patch は `admission_cases._init_repo` seam を使う一方、現物には [_issued_cell_for_campaign_identity](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:1084) と `_issued_cell` seam、run-a/run-b pin が追加されている。

(b) [実測] 保存 patch の reverse check は失敗した。さらに作業 tree は「未 commit」という依頼記述と異なり、clean な commit `a0ac63690574120448b259ede9b9dca5d92d0e47` である。

(c) [推測] 現物の F1 は正しい方向に補強されているが、保存 patch と完了報告から最終 test を再構成できず、変更由来とレビュー対象 bytes の証明が崩れる。

(d) [推測] 最終 commit の test 差分から `s6-fix1.patch` を再生成し、stats の net 行数を `+248`、fix 全体を `+277` に更新する。コード修正は不要。

### 所見 2 — M15 の DW-M08 集合は probe 範囲の固定が必要（must-fix）

(a) [実測] M15 は default v4 key set 自体を変えるため、登録 contract node だけでなく多数の v4 verifier node を早期 key mismatch で赤化する。

(b) [実測] 少なくとも ownership 4 test file 内で53 nodeid、外部にも `test_s8b_floor_campaign.py` の4 nodeと `test_s8b_ratified_freeze.py::test_happy_path_resolves_and_loads` が確実に赤化する。`s8b_holdout_freeze._validate_floor_inputs` の利用者にも波及する。

(c) [推測] 親の20-file集合を mutation probe に使う場合、下記 E15を完全集合として登録すると DW-M08 の一致検査に失敗する。

(d) [推測] mutation manifest に collect対象を明記し、M15だけはその collect集合に対する実測 red setを事前期待へ固定する。

nit はありません。

## 弱体化・不変性

- [実測] base `50dbf9158` からの4 test file差分は、それぞれ `+123/-0`、`+535/-0`、`+62/-0`、`+596/-0`。不変 pin 表の4 fileで既存行削除は0件。
- [実測] assertion の反転、緩和、追加された skip/xfail はない。fix patch中の削除は手書き validator除去、同値コード置換、F3 assertion移動であり、base assertionは残る。
- [実測] production 4 fileの `git diff 50dbf9158` は `s5-integrated.patch` のproduction部分と byte一致した。
- [実測] `git diff --check` と4 test fileのAST parseは成功した。
- [実測] pytestは本レビューでは実走していない。

## 変異帰属表

略号は `C=test_attempt_registry_core_s8b_profile.py`、`R=test_s8b_attempt_registry.py`、`K=test_s8b_floor_contract.py`、`S=test_s8b_floor_stats.py`。完全赤集合はまずownership 4 fileを対象とした静的予測である。

| ID | old 逐語の所在 | 観測 nodeid | 帰属成立 / 遮る層 | 完全赤集合の静的予測 |
|---|---|---|---|---|
| M1 | [core:295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:295) `if actual_keys != ATTEMPT_REGISTRY_PREFIX_PROOF_KEYS:` | `C::test_attempt_registry_prefix_proof_rejects_extra_key` | [実測] 成立。extra key は後段で拒否されない。missing-key は後段 digest が拒否するが reason が変わる。 | [推測] 観測 nodeと `C::test_attempt_registry_prefix_proof_rejects_missing_key`。 |
| M2 | [core:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:315) `freeze_sha256 = _digest(...)` 3行 | `C::test_attempt_registry_prefix_proof_rejects_each_field_type[digest-freeze-sha256-int]` | [実測] anchor-localなtruthy/passthrough変異なら成立。 | [推測] 観測 nodeと `C::test_attempt_registry_prefix_proof_rejects_invalid_digest[freeze_sha256]`。 |
| M3 | [core:325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:325) `row_count < 1` | `C::test_attempt_registry_prefix_proof_rejects_zero_row_count` | [実測] 成立。zero以外はvalid。 | [推測] 観測 nodeのみ。 |
| M4 | [core:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:334) `if chain_head_sha256 == _ZERO_SHA256:` | `C::test_attempt_registry_prefix_proof_rejects_zero_head` | [実測] 成立。zeroはhex64 gateを通る。 | [推測] 観測 nodeと `S::test_pure_verifier_accepts_v5_with_independent_prefix_proof`。 |
| M5 | [registry:974](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:974) `return core.load_attempt_registry(...)` 5行 | `R::test_attempt_registry_prefix_rejects_malformed_tail_after_n` | [実測] 成立。最初のparse失敗で停止する寛容decodeだけがmalformed tailを無視する。 | [推測] 観測 nodeのみ。 |
| M6 | [registry:974](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:974) 同じ5行 | `R::test_attempt_registry_prefix_rejects_broken_chain_after_n` | [実測] 成立。decode-onlyではcanonical JSONのbroken chainを受理する。 | [推測] 観測 nodeと `R::test_attempt_registry_prefix_unrecomputed_prefix_tamper_reaches_chain_gate`。 |
| M8 | [registry:1043](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1043) `rows[row_count - 1]["event_sha256"] != chain_head_sha256` | `R::test_attempt_registry_prefix_rejects_reported_head_tamper` | [実測] 成立。test内でfull replay成功を直接確認済み。 | [推測] 観測 nodeと `S::test_live_v5_real_registry_rejects_reported_other_generation`。後者はpure比較で拒否を残すが、期待したinspector例外でなくなる。 |
| M9 | [registry:1043](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1043) `rows[row_count - 1]` | `R::test_attempt_registry_prefix_inspection_accepts_valid_later_append` | [実測] 成立。production classificationをN=3の後へ追加している。 | [推測] 観測 nodeのみ。 |
| M10 | [registry:941](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:941) v2 schema guard 3行 | `R::test_attempt_registry_prefix_rejects_synthetic_v1_at_generation_path` | [実測] 成立。production recovery authority、profile再構成、core replayがすべて成功する。遮る層なし。 | [推測] 観測 nodeのみ。 |
| M11 | [contract:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_contract.py:96) `_RESULT_V5_KEYS = _RESULT_V4_KEYS \| {"attempt_registry"}` | `K::test_result_v4_key_contract_is_mode_conditional_and_exact` | [実測] 成立。下層key setを直接比較する。 | [推測] E11、13 nodeid。 |
| M12 | [stats:801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:801) `if reported_attempt_registry != independent_attempt_registry:` | `S::test_v5_rejects_reported_prefix_head_tamper` | [実測] 成立。pure verifier直接でshape/headerはvalid。 | [推測] 観測 node、`S::test_v5_rejects_proof_binding_mismatch[schedule]`、`S::test_live_v5_calls_inspector_and_compares_reported_to_independent_proof`。 |
| M13 | [stats:1134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:1134) v5-only guard 4行 | `S::test_live_v4_does_not_call_attempt_registry_inspector` | [実測] 成立。局所 validator seam が旧遮断層を除き、inspector tripwireへ到達させる。 | [推測] 観測 nodeと `S::test_live_verifier_rejects_result_v4_unexpected_top_level_key`。 |
| M14 | [stats:1150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:1150) `expected_binding = _attempt_profile.S8BAttemptBinding(...)` 7行 | `S::test_live_v5_real_registry_rejects_reported_other_generation` | [実測] 成立。正常実装はAを選択、変異だけがreported Bをreplayして受理する。 | [推測] 観測 nodeとfake inspector node `S::test_live_v5_calls_inspector_and_compares_reported_to_independent_proof`。 |
| M15 | [contract:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_contract.py:88) `_RESULT_V4_KEYS = frozenset({` | `K::test_result_v4_key_contract_is_mode_conditional_and_exact` | [実測] 受理集合への帰属は成立するが、default v4全体へ波及する。 | [推測] E15、ownership内53 nodeid。20-file集合ではさらに増える。 |
| M16 | [stats:777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:777) freeze header比較4行 | `S::test_v5_rejects_artifact_header_freeze_tamper` | [実測] 成立。artifact headerだけが変わり、proof/expectedは同一。 | [推測] 観測 nodeと診断 node `S::test_v5_rejects_proof_binding_mismatch[freeze]`。 |
| M17 | [core:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:310) `if registry_schema != ATTEMPT_REGISTRY_PREFIX_REGISTRY_SCHEMA:` | `C::test_attempt_registry_prefix_proof_rejects_wrong_registry_schema` | [実測] 成立。 | [推測] 観測 nodeと `C::test_attempt_registry_prefix_proof_rejects_each_field_type[literal-registry-schema-none]`。 |
| M18 | [registry:889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:889) `root = admission.shared_admission_root(Path(repo_root))` | `R::test_attempt_registry_prefix_inspection_is_read_only_by_construction` | [実測] 成立。`_entry_paths`、provision、exclusive lock、fsyncをtripwire化している。 | [推測] 観測 nodeと `R::test_attempt_registry_prefix_rejects_unavailable_root_without_provisioning[root]`、`[lock]`。 |

[実測] M7は登録外のまま。長さ検査を消しても後段添字アクセスが拒否を残す。

### E11

[推測] M11の13 nodeidは、contract観測 nodeに加え、次の12件。

- `S::test_pure_verifier_accepts_v5_with_independent_prefix_proof`
- `S::test_pure_verifier_rejects_v5_without_expected_attempt_registry`
- `S::test_v5_rejects_missing_attempt_registry_proof`
- `S::test_v5_rejects_reported_prefix_head_tamper`
- `S::test_v5_rejects_artifact_header_freeze_tamper`
- `S::test_v5_rejects_artifact_header_protocol_tamper`
- `S::test_v5_rejects_proof_binding_mismatch[freeze|protocol|schedule]`
- `S::test_live_v5_absent_proof_validator_seam_is_reachable`
- `S::test_live_v5_calls_inspector_and_compares_reported_to_independent_proof`
- `S::test_live_v5_real_registry_rejects_reported_other_generation`

### E15

[推測] Ownership 4 file内では contract観測 nodeに加え、`S` の46 function family、52 nodeidが赤になる。

- v4 contract/live: `test_pure_verifier_rejects_v4_attempt_registry_as_extra_key`、`test_pure_verifier_rejects_v4_expected_attempt_registry`、`test_live_v4_does_not_call_attempt_registry_inspector`、`test_live_verifier_rejects_result_v4_unexpected_top_level_key`
- v4正例・perf: `test_verify_accepts_consistent_artifact`、`test_pilot_degraded_preserves_legacy_shape_without_perf_observation`、`test_official_degraded_requires_and_consumes_perf_observation`、`test_official_degraded_keeps_all_five_internal_consistency_conditions`、`test_official_perf_present_keeps_legacy_exact_shape`、`test_degraded_floor_stats_require_consumed_throughput_claim`、`test_degraded_floor_stats_bind_run_cmd_from_same_result`、`test_degraded_floor_stats_bind_raw_counters_from_same_result`
- session/perf負例: `test_verify_rejects_integrity_violation_with_valid_claim`、`test_verify_rejects_false_rep_integrity_exclusion`、`test_verify_rejects_exempt_session_exclusion_class_tamper[competing|launch]`、`test_verify_rejects_completed_measure_disguised_as_unmeasured_exemption`、`test_verify_rejects_normalizable_session_scalar_types[seq-string|reps-float|failures-string|retry-float]`、`test_verify_rejects_perf_required_not_required_claim`、`test_verify_rejects_counter_status_missing_contradiction`、`test_verify_rejects_bool_in_rep_observation[returncode-False|rep_index-False]`、`test_verify_rejects_negative_perf_counter`、`test_verify_rejects_unknown_or_missing_rep_evidence[unknown|missing_observation]`、`test_verify_accepts_zero_perf_counters`
- artifact負例: `test_verify_detects_tampered_floor_pair`、`test_verify_rejects_ghost_holdout_floor`、`test_verify_detects_diagnostics_cells_tamper_and_injected_key`、`test_verify_rejects_extra_key_in_floors_entry`、`test_verify_rejects_empty_artifact`、`test_verify_rejects_missing_holdout_cell`、`test_verify_rejects_threshold_selfreport_mismatch`、`test_verify_rejects_reps_selfreport_downgrade`、`test_verify_detects_false_exclusion`、`test_verify_detects_anomaly_hiding`、`test_verify_detects_reason_swap_to_partial`、`test_verify_rejects_unknown_reason`、`test_verify_detects_diagnostics_machine_anomaly_tamper`、`test_verify_detects_cell_stat_tamper`、`test_verify_rejects_cellid_collision_across_coords`、`test_verify_rejects_missing_expected_protocol_key`
- binary/admission/schema: `test_verify_rejects_duplicate_binary_for_existing_pair_without_expected_binaries`、`test_verify_rejects_unknown_binary_cell_id_without_expected_binaries`、`test_verify_rejects_binary_cell_id_bound_to_different_pair_without_expected_binaries`、`test_verify_rejects_empty_binaries_without_expected_binaries`、`test_verify_rejects_expected_holdout_without_exactly_one_sort_best`、`test_pure_verifier_rejects_admission_different_from_external_expected`、`test_pure_verifier_rejects_legacy_result_schema`

[実測] 指定された全anchorはfull blockとして各1箇所だけ存在する。M5/M6とM8/M9は同一anchorを共有する。M10の裸の `genesis.get("schema_version")` は別関数にもあるが、指定3行guardは1箇所だけである。

## 総括

- [実測] F1〜F7: closed 7、partial 0、regressed 0。
- [実測] 新規 blocker 0、新規 must-fix 2。
- [実測] production変更が必要な所見はない。
- [実測] 不変pin、既存assertion、production bytesは維持された。
- [実測] pytestは本レビューでは未実走。
- [推測] コード内容はGO相当だが、fix patch/reportの不一致とM15のDW-M08範囲未固定が残る。
- 判定: **NO-GO**。