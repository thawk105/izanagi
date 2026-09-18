## 総括

- 指定の2ファイルのみ変更。production新規関数6本、新規nodeid 14本。
- 自己検証：両ファイルのAST検査、`git diff --check`は成功。
- テスト直接呼出しの実走は0件。新規14件＋変更した既存1件は未実走。
- M1〜M7の変異実走も未実施。KILLEDとは申告しません。
- 構文検査で見つかった1件は修正済み。テストの赤／緑は未判定。
- commit・docs変更なし。**実装済み・未実走であり、closedではありません。**

## 変更点

[dispatch_compute.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2676-impl/tools/pegasus/dispatch_compute.py)：

- env名、猶予定数3個、job scriptのSHA束縛export、child_envからのpopを追加。
- `_job_run`のexcept連鎖後、isolation失敗return前にwrapper呼出しを追加。
- 以下6関数を追加。

| 関数 | 内容 |
|---|---|
| `_read_session_process` | 最後の`)`でcommを分離してstatを解析 |
| `_list_session_residuals` | session・除外集合・user namespaceによる候補列挙 |
| `_signal_session_process` | pidfd送信とエラー記録 |
| `_poll_session_processes` | POLLINによる終了観測 |
| `_sweep_job_session` | TERM→猶予→KILL→猶予、再列挙、集計、fd解放 |
| `_maybe_sweep_job_session` | SHA一致判定、祖先集合、固定定数の配線、例外記録 |

対象情報はtraceの`process`に格納し、最上位`pid`は発行者を維持しました。`main`、result schema、既存envelope照合条件は変更していません。

[test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2676-impl/orchestrator/tests/test_pegasus_dispatch_compute.py)：

- `_job_run_with_mocked_child`へ任意の環境・子例外注入を追加。既存の既定値と返却契約を維持。
- 別session内の実process fixture、fake `/proc`・pidfd fixtureを追加。
- 既存script検査へexportの順序assertを追加。

## テスト

新規nodeidはすべて`orchestrator/tests/test_pegasus_dispatch_compute.py::`配下です。

```text
test_session_sweep_terminates_attributed_orphan_and_preserves_others
test_session_sweep_kills_sigterm_ignoring_orphan
test_session_sweep_rescans_for_late_orphan
test_session_stat_parses_spaced_parenthesized_comm
test_session_sweep_without_opt_in_does_not_touch_processes
test_session_sweep_ancestry_unreadable_aborts
test_session_sweep_rechecks_identity_before_signal
test_session_sweep_does_not_claim_unconfirmed_disappearance
test_session_sweep_records_signal_errors_and_zombies
test_session_sweep_stops_at_round_limit
test_job_run_sweeps_before_result_and_strips_opt_in
test_job_run_sweeps_after_isolation_failure_without_replacing_guard
test_job_run_sweep_error_preserves_child_result
test_session_residuals_filter_namespace_and_unreadable_stat
```

既存変更nodeid：

```text
test_job_script_binds_interpreter_path_repo_and_no_network_bootstrap
```

実processの3本はpipe同期、独立した準備・sweep・回収期限を持ち、固定sleepはありません。短い猶予は実sweepの引数へ渡し、production wrapperの5.0／1.0／2は別のmock検査でassertします。

実行結果：

| 検証 | 結果 |
|---|---|
| production・testのAST解析 | 2ファイル成功 |
| `git diff --check` | rc=0 |
| test moduleをimportした直接呼出し | hookが実行前に拒否 |
| 変異を適用した直接呼出し | 未実走 |
| pytest・受入全走 | 未実走 |

初回AST検査の赤は、export追加がenvelope照合文字列へ波及した構文エラー1件でした。既存照合条件へ戻し、最終AST検査は成功しています。

## 変異対応表

すべて**期待対応であり、赤化は未実測**です。nodeidは上記と同じファイルです。

| 変異 | 関数：変更前の1行 → 変更後 | 赤になる期待nodeid |
|---|---|---|
| M1 | `_job_run`：`_maybe_sweep_job_session(request_sha256)` → `pass` | `test_job_run_sweeps_before_result_and_strips_opt_in` |
| M2 | `_maybe_sweep_job_session`：`excluded = {ancestor["pid"] for ancestor in ancestors}` → `excluded = {os.getpid()}` | `test_session_sweep_terminates_attributed_orphan_and_preserves_others` |
| M3 | `_maybe_sweep_job_session`：`if request_sha256 is None or os.environ.get(_JOB_SESSION_SWEEP_ENV) != request_sha256:` → `if False:` | `test_session_sweep_without_opt_in_does_not_touch_processes` |
| M4 | `_sweep_job_session`：`_signal_session_process(fd, record, signal.SIGKILL)` → `pass` | `test_session_sweep_kills_sigterm_ignoring_orphan` |
| M5 | `_poll_session_processes`：`events = poller.poll(math.ceil(remaining * 1000))` → `events = [(fd, select.POLLIN) for fd in pending]` | `test_session_sweep_does_not_claim_unconfirmed_disappearance` |
| M6 | `_sweep_job_session`：`for round_index in range(rounds):` → `for round_index in range(1):` | `test_session_sweep_rescans_for_late_orphan` |
| M7 | `_list_session_residuals`：`attributed = user_ns is not None and user_ns != own_user_ns` → `attributed = True` | `test_session_sweep_terminates_attributed_orphan_and_preserves_others` |

M2の裁定中の「Lが死ぬ」は、Lとscannerが同じuser namespaceであるfixtureでは成立しません。帰属述語がLを保護するためです。指定nodeidに**実wrapperが渡した除外集合へLとscannerが含まれるassert**を追加しました。Lの生存assertも維持しています。

## 波及

共有fixtureでは`_job_run_with_mocked_child`のみ変更しました。`_actual_job_run`、`_write_bound_job_run_request`、`_make_bound_xdist_case`は変更していません。SHA不一致ではwrapperが早期returnする構造です。

既存の`_job_run`直接・helper経由callerを静的に列挙すると以下です。すべて同じtestファイル内で、各名前の先頭は`test_`です。

```text
job_run_passes_sidecar_and_auto_off_to_tests_child
m5_dual_layer_interpreter_rejection_changes_acceptance_only_together
inspected_child_result_operations_are_kernel_rejected
inspected_child_cannot_rename_ancestors_but_can_write_inside_them
isolation_mount_failure_does_not_launch_child_and_leaves_red_guard
isolation_status_failure_is_infra_and_not_a_child_rc
isolated_exec_failure_is_infra_and_not_child_rc_16
isolated_child_identity_matches_direct_execution
job_result_keys_and_child_rc
job_directory_fsync_failure_returns_infra_with_failure_trace
guard_create_failure_never_reaches_isolated_launcher
parent_owned_result_publish_uses_actual_child_rc
real_child_rc_16_is_not_confused_with_isolation_infra
real_child_signal_is_published_from_wait_status
result_publish_failure_is_infra_and_guard_remains
mutation_child_reads_marker_from_read_only_submission_dir
bound_child_imports_xdist_from_validated_appended_root
job_run_emits_exact_runner_binding_report_for_bound_request
unbound_tests_request_keeps_pathname_execution
job_run_rejects_allowlist_external_environment_before_child
parent_cannot_inject_mutation_marker_through_request_environment
valid_current_and_v1_environment_overlays_survive_child_enforcement
mutation_argv_policy_fires_independently_in_job_run
mutation_structure_policy_fires_independently_in_job_run
job_run_closes_stdin_uses_repo_cwd_and_cleans_mutation_env
m10_mutation_child_receives_compute_minted_marker_only
m9_non_mutation_children_never_receive_marker
generic_job_run_executes_direct_argv_with_clean_contract
generic_job_run_refuses_non_compute_before_child
job_run_rejects_request_hash_mismatch_before_child
unbound_new_request_is_rejected_but_inflight_v2_tests_survives
provenance_task_removes_recording_markers_at_every_hop
job_run_accepts_v1_request_as_tests_task
job_run_passes_python_dont_write_bytecode_env_to_tests_child
job_run_rejects_unknown_schema_and_task
job_run_launches_task_specific_child_script
```

加えて、`main`経由の公開CLI検査は`test_public_three_arg_job_run_requires_bound_pbs_envelope`と`test_public_job_run_cli_rejects_unbound_arbitrary_request_path`です。

`_job_script`出力を検査する既存テスト：

```text
test_m7_job_script_unset_isolated_redundant_gate
test_job_script_preserves_sidecar_and_auto_off
test_job_script_binds_interpreter_path_repo_and_no_network_bootstrap
test_fa15_job_name_logs_match_job_script_and_are_collected
test_compute_marker_is_cross_namespace_evidence_without_release_handshake
test_job_script_does_not_export_mutation_attempt_marker
test_parent_binds_canonical_request_hash_into_script_result_and_receipt
test_provenance_task_removes_recording_markers_at_every_hop
```

`_job_trace`の事象列を厳密比較する既存テストは**存在します**：

- `test_result_trace_brackets_real_file_and_directory_fsync`
- `test_result_trace_does_not_claim_failed_directory_fsync_completed`

事象の有無・末尾を検査するもの：

- `test_job_directory_fsync_failure_returns_infra_with_failure_trace`

これらの期待値は変更していません。

## 未実走・限界

- 新規14件、変更した既存1件、上記consumer、M0〜M7、受入全走は未実走です。
- 指定された「2変異以上の赤化実測」は達成できていません。
- 計算ノード2走は親の担当として未実施です。
- 実process fixtureの成立、実負荷下の期限、変異の検出力は確認が必要です。
- 読めないstatはsession所属を確定できないため、signalせず不明記録として扱います。

自動実行審査の`guard_bash`が、test moduleをimportして直接呼び出す自己検証を「Pegasusログインノード上の未登録実行体」として拒否しました。拒否を迂回せず、実行できたAST検査と静的検査までを報告しています。