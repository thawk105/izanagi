# 恒久保留の追加一覧 — ユーザー提示 (D335)

本 wave (`dev-wave-t989-t932-snapshot-cost`、2026-08-16) が新規に登録した保留である。
**D335 は「正しさゲートを担うテストを保留する場合は保留一覧でユーザーへ提示する」ことを要求している。** 下の全件が `correctness_gate=True` であり、解除条件は `explicit-user-command-only` (ユーザーの明示命令のみ) である。

- 追加件数: **26**（登録後の総数 56）
- 軸を訂正した既存項目: **14**（解除はしていない）

## 追加した保留

### `test_real_repo_serialization.py` — 1 件

- **`test_protocol_builder_repo_tree_guard_is_wired_to_real_root`**
  - 成長軸: `tracked_files`
  - 保留理由: Runs full real-repository git status snapshots before and after the action, so cost grows with tracked files.
  - **同時に止まる固定検査**: Holding this node also removes fixed-size checks for exact ROOT wiring, single guard invocation, and builder/writer execution inside that guard.

### `test_s1_known_axes_freeze.py` — 9 件

- **`test_build_document_is_self_consistent_and_detects_tamper`**
  - 成長軸: `output_artifacts`
  - 保留理由: Builds or verifies the real known-axes freeze by globbing and parsing campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node removes its fixed self-consistency and single-field tamper rejection checks.
- **`test_generate_refuses_existing_freeze`**
  - 成長軸: `output_artifacts`
  - 保留理由: Builds or verifies the real known-axes freeze by globbing and parsing campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node removes its fixed create-only refusal check.
- **`test_generate_selects_registered_expected_points`**
  - 成長軸: `output_artifacts`
  - 保留理由: Builds or verifies the real known-axes freeze by globbing and parsing campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node removes its fixed golden checks for registered P2, backoff, and sort selections.
- **`test_s1b_pairing_rejects_mismatched_flags`**
  - 成長軸: `output_artifacts`
  - 保留理由: Builds or verifies the real known-axes freeze by globbing and parsing campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node removes its fixed S-1b mismatched-flags rejection check.
- **`test_verify_rejects_foreign_ccbench_pin`**
  - 成長軸: `output_artifacts`
  - 保留理由: Builds or verifies the real known-axes freeze by globbing and parsing campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node removes its fixed held/released ccbench-pin positive control.
- **`test_verify_rejects_generator_sha_tamper`**
  - 成長軸: `output_artifacts`
  - 保留理由: Builds or verifies the real known-axes freeze by globbing and parsing campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node removes its fixed generator-hash tamper rejection check.
- **`test_verify_rejects_non_ancestor_head`**
  - 成長軸: `output_artifacts`
  - 保留理由: Builds or verifies the real known-axes freeze by globbing and parsing campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node removes its fixed non-ancestor HEAD rejection check.
- **`test_verify_rejects_one_byte_freeze_tamper`**
  - 成長軸: `output_artifacts`
  - 保留理由: Builds or verifies the real known-axes freeze by globbing and parsing campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node removes its fixed one-byte freeze tamper rejection check.
- **`test_verify_rejects_tampered_source_copy`**
  - 成長軸: `output_artifacts`
  - 保留理由: Builds or verifies the real known-axes freeze by globbing and parsing campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node removes its fixed copied-source hash tamper rejection check.

### `test_s1_measurement_freeze.py` — 11 件

- **`test_build_document_rejects_tampered_known_axes_semantics`**
  - 成長軸: `output_artifacts`
  - 保留理由: Consumes the module-scoped real known-axes fixture, which globs and parses campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node also prevents the shared module fixture from starting, so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent golden, and K.verify_document stop too. The node's fixed known-axes semantic tamper rejection check stops too.
- **`test_generate_builds_registered_cells_comparisons_and_schedule`**
  - 成長軸: `output_artifacts`
  - 保留理由: Consumes the module-scoped real known-axes fixture, which globs and parses campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node also prevents the shared module fixture from starting, so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent golden, and K.verify_document stop too. The node's fixed checks for 18 cells, 12 comparisons, schedule shape, seeds, and operating-point flags stop too.
- **`test_generate_refuses_existing_freeze`**
  - 成長軸: `output_artifacts`
  - 保留理由: Consumes the module-scoped real known-axes fixture, which globs and parses campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node also prevents the shared module fixture from starting, so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent golden, and K.verify_document stop too. The node's fixed measurement create-only refusal check stops too.
- **`test_receipt_exists_but_measurement_verify_stays_legacy_strict`**
  - 成長軸: `output_artifacts`
  - 保留理由: Consumes the module-scoped real known-axes fixture, which globs and parses campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node also prevents the shared module fixture from starting, so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent golden, and K.verify_document stop too. The node's fixed legacy-verifier isolation from the T-080 adapter stops too.
- **`test_recorded_ccbench_pin_hold_and_release_positive_control`**
  - 成長軸: `output_artifacts`
  - 保留理由: Consumes the module-scoped real known-axes fixture, which globs and parses campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node also prevents the shared module fixture from starting, so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent golden, and K.verify_document stop too. The node's fixed recorded-pin hold and release positive control stops too.
- **`test_s1b_pairing_rejects_mismatched_flags`**
  - 成長軸: `output_artifacts`
  - 保留理由: Consumes the module-scoped real known-axes fixture, which globs and parses campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node also prevents the shared module fixture from starting, so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent golden, and K.verify_document stop too. The node's fixed measurement S-1b mismatched-flags rejection check stops too.
- **`test_schedule_is_balanced_and_reproducible`**
  - 成長軸: `output_artifacts`
  - 保留理由: Consumes the module-scoped real known-axes fixture, which globs and parses campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node also prevents the shared module fixture from starting, so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent golden, and K.verify_document stop too. The node's fixed schedule balance and reproducibility checks stop too.
- **`test_verify_rejects_known_axes_material_tamper`**
  - 成長軸: `output_artifacts`
  - 保留理由: Consumes the module-scoped real known-axes fixture, which globs and parses campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node also prevents the shared module fixture from starting, so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent golden, and K.verify_document stop too. The node's fixed known-axes material-hash tamper rejection check stops too.
- **`test_verify_rejects_one_byte_freeze_tamper`**
  - 成長軸: `output_artifacts`
  - 保留理由: Consumes the module-scoped real known-axes fixture, which globs and parses campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node also prevents the shared module fixture from starting, so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent golden, and K.verify_document stop too. The node's fixed one-byte measurement freeze tamper rejection check stops too.
- **`test_verify_rejects_one_byte_workload_flag_tamper`**
  - 成長軸: `output_artifacts`
  - 保留理由: Consumes the module-scoped real known-axes fixture, which globs and parses campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node also prevents the shared module fixture from starting, so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent golden, and K.verify_document stop too. The node's fixed one-byte workload-flag tamper rejection check stops too.
- **`test_verify_rejects_stats_implementation_tamper`**
  - 成長軸: `output_artifacts`
  - 保留理由: Consumes the module-scoped real known-axes fixture, which globs and parses campaign artifacts, so cost grows with output artifacts.
  - **同時に止まる固定検査**: Holding this node also prevents the shared module fixture from starting, so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent golden, and K.verify_document stop too. The node's fixed statistics-implementation hash tamper rejection check stops too.

### `test_s8b_binding_driftguards.py` — 1 件

- **`test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal`**
  - 成長軸: `commits`
  - 保留理由: Runs real-repository receipt and active-generation history resolution over the reachable commit graph, so cost grows with commit history.
  - **同時に止まる固定検査**: Holding this node also removes the fixed-size binding-manifest schema refusal aggregation check.

### `test_s8b_oracle_driver.py` — 3 件

- **`test_active_resolution_and_manifest_structure_refusals_are_aggregated`**
  - 成長軸: `commits`
  - 保留理由: Runs real-repository receipt and active-generation history resolution over the reachable commit graph, so cost grows with commit history.
  - **同時に止まる固定検査**: Holding this node also removes the fixed-size independent-refusal aggregation and zero-side-effect checks.
- **`test_nonnull_floor_without_active_generation_is_refused`**
  - 成長軸: `commits`
  - 保留理由: Runs real-repository receipt and active-generation history resolution over the reachable commit graph, so cost grows with commit history.
  - **同時に止まる固定検査**: Holding this node also removes the fixed-size no-active error translation, no-prepare, no-evaluate, and no-write checks.
- **`test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing`**
  - 成長軸: `commits`
  - 保留理由: Runs real-repository receipt and active-generation history resolution over the reachable commit graph, so cost grows with commit history.
  - **同時に止まる固定検査**: Holding this node also removes fixed-size refusal, no-prepare, no-evaluate, and zero-output checks.

### `test_s8b_protocol_builder.py` — 1 件

- **`test_build_and_write_leave_repo_tree_unchanged`**
  - 成長軸: `tracked_files`
  - 保留理由: Runs full real-repository git status snapshots before and after the action, so cost grows with tracked files.
  - **同時に止まる固定検査**: Holding this node also removes fixed-size top-level and nested writer checks and the frozen-output refusal check.

## 軸を訂正した既存項目 (解除ではない)

[T-989] が `git clone --no-hardlinks` を除去したため、`commits` 軸を根拠にしていた理由文が事実と食い違うようになった。2026-08-12 の 3 wave 合意「除去が完了しても台帳 entry は自動で外さない」に従い**解除はせず**、軸と理由文だけを現実へ合わせた。

- `test_codex_reasoning_ab.py::test_agent_sandbox_binds_exclude_attempt_receipt_directory`: `commits` → `output_artifacts`
- `test_codex_reasoning_ab.py::test_attempt_four_is_rejected_before_launch`: `commits` → `output_artifacts`
- `test_codex_reasoning_ab.py::test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure`: `commits` → `output_artifacts`
- `test_codex_reasoning_ab.py::test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation`: `commits` → `output_artifacts`
- `test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases`: `commits` → `output_artifacts`
- `test_codex_reasoning_ab.py::test_m1_snapshot_head_pin_is_independent`: `commits` → `output_artifacts`
- `test_codex_reasoning_ab.py::test_m3_focus_artifact_directions`: `commits` → `output_artifacts`
- `test_codex_reasoning_ab.py::test_m3_ignored_extra_and_missing`: `commits` → `output_artifacts`
- `test_codex_reasoning_ab.py::test_m3_snapshot_mode_change`: `commits` → `output_artifacts`
- `test_codex_reasoning_ab.py::test_m3_symbolic_head_is_required`: `commits` → `output_artifacts`
- `test_codex_reasoning_ab.py::test_parent_numstat_controls_remain_pinned`: `commits` → `output_artifacts`
- `test_codex_reasoning_ab.py::test_pos_neg_submodule_initialization_state_mismatch_is_rejected`: `commits` → `output_artifacts`
- `test_codex_reasoning_ab.py::test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested`: `commits` → `output_artifacts`
- `test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment`: `commits` → `output_artifacts`

