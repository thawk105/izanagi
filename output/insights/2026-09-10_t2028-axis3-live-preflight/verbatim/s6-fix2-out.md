## 復元の結果 (原文のまま通ったか)

通りませんでした。原文を逐語復元して自走 harness を実行した結果、対象だけが失敗し、`1 failed, 121 passed` でした。

## 通らなかった場合の原因と置き換え (file:line)

F2 により HTTP 503 は inline 再試行されません。

- [related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:6960) は HTTP response が返れば status にかかわらず row の試行を終了します。
- WAL validator は同一 stream の後続 attempt を、直前が `live_transport` 失敗の場合だけ受理します。[related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py:6545)
- したがって、原文の `[503, 200]` は line 6551 で `bundle_preflight_sequence` となり、`initial_plan_complete` 以降の assert へ到達しませんでした。

置き換えでは元のテスト名を維持し、後続 row の失敗を現行契約で再試行可能な `live_transport` に変更しました。[test_related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:3125)

以下の性質は維持しています。

- 後続 row の transport 再試行が完了すること
- availability evidence が sequence index 0 のままであること
- index 0 が固定 ID `AX3A1-L-ID-01@openalex` であること

HTTP 503 後の成功を拒否する性質は、隣接する独立テストでも固定されています。[test_related_work_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py:3146)

実装側は変更していません。

## 関数名集合の差分 (削除ゼロの確認)

`HEAD` の基底 test file と現行 test file を AST で比較しました。

- 基底: 94関数
- 現行: 108関数
- 削除・改名: 0件
- 追加: 14件

追加14件はすべて維持されています。

- `test_cooldown_and_missing_limiter_state_survive_new_instance`
- `test_final_retryable_tail_remains_nonfinalizable`
- `test_host_pacing_uses_actual_pre_send_time_and_persists_across_limiters`
- `test_http_failure_cannot_be_followed_by_inline_success`
- `test_live_session_records_issue_time_immediately_before_transport_send`
- `test_packed_wal_commits_transport_failure_without_pending_intent`
- `test_preflight_does_not_swallow_non_transport_contract_errors`
- `test_preflight_exhausts_four_dblp_transport_attempts_then_cools_down`
- `test_preflight_report_observed_interval_is_nonblocking_n3`
- `test_preflight_retries_live_transport_and_never_retries_http_status`
- `test_preflight_wal_accepts_four_transport_attempts_and_rejects_fifth`
- `test_resume_pacing_intervals_are_unmeasured_null`
- `test_transport_exception_materializes_pending_attempt_before_reraise`
- `test_wire_budget_rejection_precedes_attempt_intent`

## 実走したテスト (nodeid と結果)

原文復元時:

- `orchestrator/tests/test_related_work_search.py::test_later_row_retry_does_not_replace_availability_evidence`
- 結果: `FAILED`
- 全体: `1 failed, 121 passed in 73.24s`

置き換え後:

- 同 nodeid: `PASSED`
- 単独選択: `1 passed, 121 deselected in 6.89s`
- 全 harness: `122 passed in 75.06s`

実行は指定された自走 harness を使用し、実時間 sleep は使用していません。

## 総括

削除されたテスト名と保護対象を復元し、現行契約に合わせて HTTP 503 再試行から transport 例外再試行へ意味だけを変更しました。編集は test file のみです。

既存期待値は変更しておらず、catalog digest も指定値 `7dd14814ecd3a924d61ebfee707d604556624db639240318a95ce49e44185a58` と一致しました。docs、実装、台帳、commit、pushには触れていません。