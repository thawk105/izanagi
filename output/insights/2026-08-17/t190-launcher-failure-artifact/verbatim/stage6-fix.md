実装は F1〜F11 すべて反映済みです。変更は指定された 2 ファイルだけで、docs 編集・commit はありません。静的検査は通過しましたが、Pegasus の `qstat` 障害により pytest は未実走です。

### F1〜F11

| 項目 | 結果 | 主な箇所 |
|---|---|---|
| F1 | 修正。launcher 主体フラグを送信済み signal の有無から導出。forced-stop 分岐に入っても signal 0 件なら false となる production 経路負例を追加 | [codex_worker_launch.py:391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:391)、[test_codex_worker_launch.py:4094](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:4094) |
| F2 | 修正。`_worker_module.os` の置換を廃止。worker の identity 検証を使いながら TERM/KILL と callback を launcher 内へ局所化。並行帰属テストを追加 | [codex_worker_launch.py:1449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1449)、[test_codex_worker_launch.py:4028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:4028) |
| F3 | 修正。最終 `observe` 後に時刻を再取得。production `_attempt_loop` と制御 clock を通る exact duration node を追加 | [codex_worker_launch.py:1808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1808)、[test_codex_worker_launch.py:4239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:4239) |
| F4 | 修正。copy、path-map、index を独立 3 node へ分割 | [test_codex_worker_launch.py:1779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1779)、[同:1806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1806)、[同:1817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1817) |
| F5 | 修正。archive root を故意に壊した子 pytest で、元の rc mismatch と `INTERNALERROR` 不在を外側から検査 | [test_codex_worker_launch.py:2209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:2209)、[同:2230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:2230) |
| F6 | 修正。directory を含む全 entry を cap に算入し、上限後は descent を停止して subtree omission 1 件へ集約。無制限 `rglob` を削除。run 単位で 21 bundles／16,384 entries／512 MiB を上限化し、超過時は metadata-only | [test_codex_worker_launch.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:117)、[同:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:358)、[同:1972](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1972)、[同:2020](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:2020) |
| F7 | 修正。receipt、sidecar、attempt events/stderr/output、manifest を優先順位 0 で先にコピー。`critical_set_complete` を manifest と metadata に保存 | [test_codex_worker_launch.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:117)、[同:556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:556)、[同:1999](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1999) |
| F8 | 修正。snapshot に elapsed、model calls、CLI tokens、各 limit、判定時 job elapsed を保存 | [codex_worker_launch.py:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:576)、[test_codex_worker_launch.py:4380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:4380) |
| F9 | 修正。bounded 例外型・message・切詰め flag・call duration を追加。sidecar 不在理由を観測別 enum へ分離 | [test_codex_worker_launch.py:444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:444)、[同:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:462)、[同:2050](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:2050) |
| F10 | 修正。数値 parse failure で `on_malformed` と `on_unknown` の双方を呼び、同じ node で双方を検査 | [codex_worker_launch.py:1418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1418)、[test_codex_worker_launch.py:3886](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:3886) |
| F11 | 修正。autouse fixture から `tmp_path` 依存を除去し、hook 内の `item.funcargs` から遅延取得。対象なしなら archive しない | [test_codex_worker_launch.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:614)、[同:640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:640)、[同:1703](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1703) |

### 新設・改名した nodeid

HEAD からの最終追加・改名一覧です。

```text
orchestrator/tests/test_codex_worker_launch.py::test_concurrent_termination_observers_keep_signal_attribution_local
orchestrator/tests/test_codex_worker_launch.py::test_evidence_forced_stop_propagates_unknown_residual_to_sidecar
orchestrator/tests/test_codex_worker_launch.py::test_failure_archive_appends_index
orchestrator/tests/test_codex_worker_launch.py::test_failure_archive_bounds_exception_message_and_absence_reason
orchestrator/tests/test_codex_worker_launch.py::test_failure_archive_copies_critical_set_before_optional_files
orchestrator/tests/test_codex_worker_launch.py::test_failure_archive_copies_exact_bytes_from_new_root
orchestrator/tests/test_codex_worker_launch.py::test_failure_archive_run_budget_leaves_metadata_only_bundle
orchestrator/tests/test_codex_worker_launch.py::test_failure_archive_stops_descent_for_directory_heavy_source
orchestrator/tests/test_codex_worker_launch.py::test_failure_archive_writes_path_map
orchestrator/tests/test_codex_worker_launch.py::test_forced_stop_without_signal_is_not_launcher_initiated
orchestrator/tests/test_codex_worker_launch.py::test_group_member_count_records_malformed_without_changing_count
orchestrator/tests/test_codex_worker_launch.py::test_group_member_count_reports_identity_missing_source
orchestrator/tests/test_codex_worker_launch.py::test_group_member_count_reports_scandir_failure_source
orchestrator/tests/test_codex_worker_launch.py::test_group_member_count_reports_stat_parse_failure_source
orchestrator/tests/test_codex_worker_launch.py::test_group_member_count_reports_stat_read_failure_source
orchestrator/tests/test_codex_worker_launch.py::test_launcher_diagnostics_keeps_control_trigger_separate_from_all_conditions
orchestrator/tests/test_codex_worker_launch.py::test_launcher_diagnostics_limit_conditions_negative_and_exact_boundary
orchestrator/tests/test_codex_worker_launch.py::test_launcher_diagnostics_phase_durations_use_distinct_boundaries
orchestrator/tests/test_codex_worker_launch.py::test_launcher_diagnostics_production_phase_wiring_has_exact_durations
orchestrator/tests/test_codex_worker_launch.py::test_launcher_diagnostics_records_all_conditions_and_site_values
orchestrator/tests/test_codex_worker_launch.py::test_launcher_diagnostics_sidecar_is_outside_receipt_schema
orchestrator/tests/test_codex_worker_launch.py::test_launcher_diagnostics_sidecar_write_does_not_fsync
orchestrator/tests/test_codex_worker_launch.py::test_launcher_diagnostics_write_failure_does_not_change_control_result
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_archive_error_probe
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_byte_limit_records_omission_reason
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_copy_error_does_not_mask_failure
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_exception_safety_live
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_fixture_does_not_request_tmp_path
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_hook_ignores_item_without_tmp_path
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_limits_record_omission_reasons
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_live_wiring_probe
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_marks_timeout_source_incomplete
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_paths_are_collision_free
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_rejects_ancestor_destination
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_reporter_hook_is_tryfirst
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_reporter_ignores_handled_failure
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_reporter_live_wiring
orchestrator/tests/test_codex_worker_launch.py::test_launcher_failure_artifact_special_file_is_not_opened
orchestrator/tests/test_codex_worker_launch.py::test_unknown_residual_source_propagates_through_terminate
orchestrator/tests/test_codex_worker_launch.py::test_unknown_residual_source_propagates_without_verifying_normal_reap
```

既存 node の改名・分割は次のとおりです。

- `test_proc_scan_and_missing_identity_are_unknown` → `test_group_member_count_reports_identity_missing_source`、`test_group_member_count_reports_scandir_failure_source`
- `test_individual_proc_read_failure_is_unknown` → `test_group_member_count_reports_stat_read_failure_source`
- `test_unknown_residual_never_verifies_normal_reap` → `test_unknown_residual_source_propagates_without_verifying_normal_reap`
- 段 5 の暫定 `test_launcher_failure_artifact_reporter_archives_unhandled_call_failure` → `test_failure_archive_copies_exact_bytes_from_new_root`、`test_failure_archive_writes_path_map`、`test_failure_archive_appends_index`

### M01〜M14、P01 の完全集合

以下は最終 anchor に対する静的完全集合です。dispatch 障害により mutation 実走での動的確定は未実施です。各名前の prefix は `orchestrator/tests/test_codex_worker_launch.py::` です。

- M01:
  `test_positive_p3_exact_limit_natural_exit_is_accepted`
- M02:
  `test_positive_p3_exact_limit_natural_exit_is_accepted`、
  `test_launcher_diagnostics_limit_conditions_negative_and_exact_boundary`、
  `test_launcher_diagnostics_records_all_conditions_and_site_values`、
  `test_receipt_staging_wall_overrun_flips_to_not_accepted_and_removes_output`、
  `test_receipt_audit_wall_overrun_flips_to_not_accepted`
- M03:
  `test_launcher_diagnostics_production_phase_wiring_has_exact_durations`
- M04:
  `test_unknown_residual_source_propagates_through_terminate`、
  `test_evidence_forced_stop_propagates_unknown_residual_to_sidecar`
- M05:
  `test_launcher_failure_artifact_reporter_hook_is_tryfirst`、
  `test_launcher_failure_artifact_reporter_live_wiring`
- M06:
  `test_failure_archive_copies_exact_bytes_from_new_root`、
  `test_launcher_failure_artifact_paths_are_collision_free`、
  `test_launcher_failure_artifact_copy_error_does_not_mask_failure`、
  `test_failure_archive_copies_critical_set_before_optional_files`、
  `test_launcher_failure_artifact_reporter_live_wiring`
- M07:
  `test_launcher_failure_artifact_paths_are_collision_free`
- M08:
  `test_complete_receipt_publication_is_atomic_create_only_at_run_callsite`
- M09:
  `test_failure_archive_writes_path_map`
- M10:
  `test_launcher_failure_artifact_exception_safety_live`
- M11:
  `test_evidence_forced_stop_propagates_unknown_residual_to_sidecar`、
  `test_rollout_missing_after_grace_is_stopped_and_not_accepted`、
  `test_thread_missing_after_grace_kills_process_group`
- M12:
  `test_group_member_count_reports_stat_parse_failure_source`、
  `test_group_member_count_records_malformed_without_changing_count`
- M13:
  `test_failure_archive_appends_index`
- M14:
  `test_positive_p3_exact_limit_natural_exit_is_accepted`、
  `test_launcher_diagnostics_limit_conditions_negative_and_exact_boundary`
- P01:
  落ちる node は空集合。`test_launcher_diagnostics_write_failure_does_not_change_control_result` の通過を要求する正例。

### 実走結果

指定全走を 3 回実行しました。

```text
python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_codex_worker_launch.py -q -rf
```

3 回とも pytest 起動前に以下で終了しました。

```text
runner rc=16
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
```

したがって、実走した test nodeid は 0 件です。

制約 meta-test も次の 3 node を明示して 1 回 dispatch しましたが、同じ rc=16 でした。

- `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `orchestrator/tests/test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`
- `orchestrator/tests/test_plain_runner_coverage.py::test_this_metatest_is_itself_self_runnable`

実施済みの静的検査:

- 両 Python ファイルの AST parse: 成功
- test 関数 139 件、重複名なし
- `git diff --check`: 成功
- U+0300〜U+036F: 0 件
- `_worker_module.os` 代入: 0 件
- `termination_initiated_by_launcher` 代入: 0 件
- archive 内の `list(tmp_path.rglob(...))`: 0 件
- tracked 差分: 指定 2 ファイルだけ

### 既存テストへの波及

- receipt schema、`accepted` 式、`_LIMIT_REASONS`、`limit_trigger` の値と優先順位、checker rc、fixture の時間予算は変更していません。
- `supervision_drain_completed` の sampling は final drain 後へ正されました。比較述語は不変ですが、段 4 不変条件 6 のとおり実時間境界ではより新しい実測値になります。
- signal 停止順は worker 実装と同じ TERM→grace→KILL を維持し、共有 module global の置換だけを除去しました。
- autouse fixture は `tmp_path` を要求しなくなったため、従来 `tmp_path` を持たない cases の追加 directory 作成はなくなります。
- archive の run lock と容量制限は未処理 call-phase failure 時だけ発火します。緑走の copy I/O は増えません。
- 既存 assertion の反転、緩和、skip、削除はありません。
- docs、receipt consumer、`worker.py`、dispatch allowlist は未変更です。

## 総括

F1〜F11 は指定 2 ファイルへ実装し、段 4 の不変条件と docs／commit 禁止を維持しました。ただし `qstat` preflight 障害により対象 test と制約 meta-test は未実走です。状態は「実装済み・未実走」であり、テスト上の所見を closed とは申告しません。