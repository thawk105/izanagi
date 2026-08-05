実装済み・未実走です。既存の assert、期待値、skip 条件は変更していません。production・docs・禁止対象テストには触れず、commit もしていません。

### 変更した nodeid

- `test_claude_transport.py::test_success_consumer_keeps_valid_receipt_in_journal_and_report` — public 経路の明示 opt-in から得た sealed scope/admission を journal と `_finish_trial()` に渡しました。
- `test_claude_transport.py::test_opt_in_report_and_opt_out_report_field_boundaries` — 両レポートを public scope 内で生成し、launch admission を明示しました。
- `test_claude_transport.py::test_terminal_events_keep_transport_receipt` — private `_finish_trial()` / `_run_workload()` を public scope 内で実行し、admission を束縛しました。
- `test_claude_transport.py::test_p2_flag_on_run_trial_admits_compute_wrapper_with_real_providers` — `allow_unregistered_exploratory=True` を明示しました。
- `test_claude_transport.py::test_p1_flag_omitted_run_trial_has_no_transport_io_or_fields` — transport opt-out と独立に探索 opt-in を明示しました。
- `test_autonomous_trial_completeness.py::test_auditor_skip_is_journaled_and_has_no_carve_out` — 探索 opt-in を明示しました。
- `test_autonomous_trial_completeness.py::test_m4a_producer_supervisor_error_preserves_constructed_generation` — 探索 opt-in を明示しました。
- `test_autonomous_trial_completeness.py::test_completeness_failure_is_not_caught_and_report_is_not_written` — 探索 opt-in を明示しました。
- `test_autonomous_trial_completeness.py::test_role_append_io_failure_cannot_publish_incomplete_report` — 探索 opt-in を明示しました。
- `test_autonomous_trial_completeness.py::test_journal_change_after_verifier_read_is_fail_closed` — 探索 opt-in を明示しました。
- `test_role_session_isolation.py::test_fixture_run_keeps_drive_and_preview_injection` — 探索 opt-in を明示しました。
- `test_role_session_isolation.py::test_fixture_run_omitted_drivers_use_current_module_values` — 探索 opt-in を明示しました。
- `test_role_session_isolation.py::test_omitted_claude_drivers_resolve_before_finish_trial` — 探索 opt-in を明示しました。
- `test_campaign.py::test_autonomous_trial_env_run_root_and_worktree_container_gate` — CLI 2経路にフラグ、直接起動に引数を明示し、架空 `ROOT` ケースには public registry API 発行の admission を渡しました。

### 検査

`pegasus02` はログインノードのため、規律に従い pytest は実行していません。実走 nodeid はありません。

- `py_compile`: rc=0
- `git diff --check`: rc=0
- `tools/check_codex_agents.py`: rc=0
- `tools/check_docs.py`: rc=0

## 総括

- 変更した test 件数: **14件**
- pytest の rc: **未実走のためなし**
- 意図保存できなかった箇所: **なし**
- 状態: **実装済み・未実走**（`closed` とは申告しません）