静的監査結果です。pytest は指定どおり未実行です。

## 1. scope 完全性 — real

`_accounting_present` の本番呼び出しは `[dispatch_compute.py:1935](/work/1/SFC/tanab/izanagi/.claude/worktrees/t222-scheduler-group/tools/pegasus/dispatch_compute.py:1935)` と `:1946` の2箇所だけです。公開 `dispatch()` の呼び出しは次の2箇所で、シグネチャ変更は不要です。

- `tools/run_tests.py:1143,1153`
- `tools/check_ai_provenance.py:1816,1818`

ただし、同種の accounting 検証・生成経路が他にあります。

- `[silo_ladder_rung1.py:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/t222-scheduler-group/orchestrator/campaign/silo_ladder_rung1.py:153)`、`:3702`、`:3531`、`:4644`  
  Request ID／Started／Ended／Elapse を独自 regex で検証する完全な重複経路。`Group Name` は無視する。policy も SFC (`tools/pegasus/policy.json:23`)。
- `[floor_liveness.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/t222-scheduler-group/orchestrator/campaign/floor_liveness.py:30)`、`:186`、`:407`  
  4 marker の単純存在検査で `accounting_present=True` を生成し、Group Name を検証しない。
- `[collect_receipt.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/t222-scheduler-group/tools/pegasus/collect_receipt.py:27)`、`:67`、`:151`  
  scheduler stderr の accounting summary を独自 parse し、別キー `scheduler_accounting_present` を生成する。
- `[t503_restore_durability_probe.py:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/t222-scheduler-group/tools/pegasus/probes/t503_restore_durability_probe.py:296)`、`:308`  
  Request ID と scheduler terminal accounting を独自検証する。
- fixture にも `Group Name: fixture` があるが、検証対象外 (`orchestrator/tests/fixtures/silo_ladder_rung1_driver/nqsv_accounting_epilogue.txt:7`)。

少なくとも `silo_ladder_rung1` と `floor_liveness` は、今回の Group Name 束縛を scope 外に置くなら明示的な裁定が必要です。

## 2. resume 側 C1 — refuted

`dispatch_compute.py` 内に resume／monitor 相当の独立関数や `validate_nqsv_accounting` はありません。

- scheduler 監視は `_dispatch_impl` 内の loop (`:1824`)
- accounting collection も同じ `_dispatch_impl` 内 (`:1902`)
- accounting 判定は `_accounting_present` (`:924`) のみ
- `main --job-run` (`:2234`) は child launcher であり、accounting 検証経路ではない

したがって、brief の「このファイルに別 resume 経路はない」は裏付けられます。なお、外部の `floor_liveness.classify()` は項目1の別経路です。

## 3. 既存テスト網羅 — refuted

全体を `accounting|Request ID|_Scheduler\(|_accounting_present` で grep しました。

`_Scheduler(` を使うテスト関数は63件。うち61件は既定の `accounting=True`、次の2件だけ `False` です。

- `test_accounting_grace_failure_relays_collected_stdout`
- `test_accounting_grace_failure_is_invocation_only_and_does_not_latch`

既定値のテストは `_Scheduler._finish` の fixture 更新だけで足ります。`accounting=False` の2件は意図的に footer を出さないため変更不要です。

全63件:

```text
test_queue_wait_timeout_attests_child_not_started_once
test_queue_wait_timeout_without_queued_proof_attests_started
test_fast_ended_job_without_result_attests_started_when_run_was_unseen
test_receipt_persist_failure_after_red_child_attests_started_and_rc
test_child_rc_passthrough_emits_no_infra_attestation
test_success_receipt_explicitly_attests_child_started
test_dispatch_state_machine_returns_child_rc_after_accounting
test_nonzero_child_relays_stdout_to_parent_stdout
test_nonzero_child_relays_only_last_sixty_four_kib_of_stdout
test_success_relays_only_last_four_kib_of_stdout
test_child_stderr_relays_only_to_parent_stderr
test_relay_exception_does_not_change_child_rc
test_relay_exception_happens_after_receipt_is_persisted
test_missing_compute_marker_relays_collected_stdout
test_accounting_grace_failure_relays_collected_stdout
test_post_collection_exception_relays_collected_stdout
test_m7_dispatcher_request_allowlist_isolated_redundant_gate
test_tests_task_env_allowlist_carries_only_recording_transport
test_fa1_rc0_request_disappearance_is_terminal_within_one_poll
test_cleanup_signal_after_qdel_is_once_only_and_preserves_first_result
test_cleanup_claim_latch_survives_post_qdel_capture_exception
test_qstat_error_during_poll_does_not_end_or_latch_job
test_fa15_job_name_logs_match_job_script_and_are_collected
test_fa15_dispatch_script_log_names_remain_backward_compatible
test_interpreter_stage_failure_is_fail_closed_and_preserved_in_receipt
test_m6_qstat_success_without_request_skips_qdel_and_create_only_latches
test_immediate_qstat_transient_failure_retries_without_latching
test_f47_literal_not_permitted_response_skips_qdel_and_latches
test_immediate_qstat_failures_exhaust_to_infra_without_latching
test_missing_compute_marker_latches_only_after_visible_job_terminates
test_create_only_nonce_collision_is_setup_infra_rc_with_receipt
test_accounting_grace_failure_is_invocation_only_and_does_not_latch
test_success_without_any_persisted_receipt_is_infra_rc
test_scheduler_logs_are_tail_bounded_with_explicit_omission
test_hld_queue_timeout_qdels_and_receipts
test_allowed_qdel_failure_records_job_may_remain_and_warns
test_claim_cleanup_finally_latches_and_blocks_next_dispatch
test_queue_wait_starts_when_qsub_returns_not_before_preflight
test_fast_job_without_observed_run_records_queue_wait_upper_bound
test_qsub_parse_failure_discovers_request_and_attempts_qdel
test_request_id_discovery_failure_skips_gate_commands_and_warns
test_malformed_qsub_request_id_runs_no_qstat_by_id_or_qdel
test_qsub_success_signal_during_receipt_capture_discovers_and_qdels
test_scheduler_exception_after_qsub_skips_qdel_and_receipts_gate_error
test_existing_orphan_hold_blocks_before_any_scheduler_command
test_orphan_hold_lstat_error_blocks_before_any_scheduler_command
test_f47_latch_precedes_orphan_hold_and_hold_remains_independent
test_qsub_result_unobserved_discovers_and_holds_without_qdel
test_observed_nonzero_qsub_does_not_latch_orphan_hold
test_overall_walltime_plus_grace_bound_skips_qdel_for_fresh_running_job
test_queue_wait_does_not_consume_observed_run_budget
test_overall_grace_allows_done_at_observed_run_deadline
test_post_run_unknown_state_uses_first_observation_deadline
test_nonzero_qstat_run_stdout_does_not_restart_deadline
test_trusted_run_after_nonzero_run_stdout_restarts_deadline
test_unknown_scheduler_state_remains_bounded_by_overall_timeout
test_walltime_override_is_bound_to_pbs_and_total_bound
test_task_kind_enum_is_closed_and_unknown_task_is_setup_infra_rc
test_t080_e2e_opt_in_env_is_projected_into_tests_request
test_python_dont_write_bytecode_env_is_projected_into_tests_request
test_provenance_task_binds_child_script_and_empty_env_allowlist
test_provenance_task_removes_recording_markers_at_every_hop
test_tests_task_remains_default_and_receipt_records_task
```

`_Scheduler` 以外で同じ grep に該当した10件は次のとおりです。前8件は `Request ID =` を使う qstat state parser テストで、accounting footer ではありません。後2件だけが `_accounting_present` の直接契約テストです。

```text
test_scheduler_state_accepts_nqsv_full_and_abbreviated_forms
test_fresh_qstat_gate_accepts_current_state_only_snapshots
test_fresh_qstat_gate_rejects_state_vocabulary_from_wrong_field
test_fresh_qstat_gate_skips_explicit_end_snapshot
test_target_bound_gate_counts_state_whitespace_recognized_by_existing_parser
test_target_bound_gate_parser_accepts_consistent_request_and_current_state
test_target_bound_gate_parser_accepts_existing_bare_state_form
test_nonzero_qstat_with_target_que_stdout_never_bypasses_transient_gate
test_accounting_requires_matching_request_id_and_all_nqsv_fields
test_accounting_accepts_measured_nqsv_shape_only_when_id_matches
```

したがって、プランの fixture 更新＋既存2契約テストの拡張で、このテストファイル内の under-registration はありません。

## 4. receipt consumer — real（旧 v2 の意味残存）

`tools/dev_wave_wait.py` と `tools/dev_wave_land.py` は `accounting_present` / `accounting_verified` を直接読んでいません。`tools/mutation_harness.py` も scheduler stdout path だけを読みます。

実際の consumer は `[check_acceptance_reds.py:338](/work/1/SFC/tanab/izanagi/.claude/worktrees/t222-scheduler-group/tools/check_acceptance_reds.py:338)` と `:345` で、両 bool が True であることだけを確認します。新しい receipt では Group Name 検証済みという強い意味になり、直ちに壊れません。

ただし schema は v2 のまま (`dispatch_compute.py:119`, `check_acceptance_reds.py:44,312`) で、checker は stderr の Group Name を再検証しません。旧 v2 receipt の `True` を新しい意味として受理できるため、後方互換・意味の混在は実在する懸念です。

## 総括

scope は閉じていない。dispatch_compute 内の2 call と同テスト fixture はプランで足りるが、silo_ladder、floor_liveness、t503、collect_receipt に独立した accounting 経路が残る。別スキーマとして除外するか、各 policy account へ同じ束縛を適用する裁定が必要である。