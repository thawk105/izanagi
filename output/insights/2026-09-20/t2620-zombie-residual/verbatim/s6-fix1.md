## 変更点

編集は [orchestrator/tests/test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2620-unit-tests/orchestrator/tests/test_codex_worker_launch.py) のみです。

- **A1・B3・A2：1616〜1671行** — harness が launcher PID を保存。終了後に養子の状態を記録し、非 Z を SIGKILL、全養子を回収して JSON を出力。回収完了時は即終了。
- **A4：4575〜4663行** — rc・harness JSON を先に記録。receipt／sidecar 欠落は `"missing"` として単一比較へ到達。外部真値は `adoptees`、回収確認は `reaped`／`unreaped` で検査。
- **A2・B2：4676〜4706行** — finally で launcher・leader・child・zombie を停止し、生存者を最後に一括 assert。
- **B1：26行、1124〜1148行、4665〜4675行** — Callable／callback を削除し、専用 helper 内で直接起動。observe → rc 検査の順序に復元。
- **A1：4709〜4712行** — N1 も `subreaper=True`。4本すべて harness 下で実行。

期待値・test 名・N3 は維持しました。

## 実走

指定コマンドで **17 passed、199 deselected、23.05秒**。`git diff --check` も正常です。

実走 nodeid は、以下すべてに `orchestrator/tests/test_codex_worker_launch.py::` を付けたものです。

```text
test_sigterm_ignoring_child_is_killed
test_sigterm_child_pid_registration_regression_detector
test_t2620_orphan_running_is_rejected
test_t2620_orphan_zombie_is_rejected
test_t2620_sigterm_ignore_subreaper_is_rejected
test_t2620_orphan_mixed_is_rejected
test_t2620_check_receipt_rejects_residual_only_changes
test_group_member_count_reports_identity_missing_source
test_group_member_count_reports_scandir_failure_source
test_group_member_count_reports_stat_read_failure_source
test_group_member_count_reports_stat_parse_failure_source
test_group_member_count_records_malformed_without_changing_count
test_unknown_residual_source_propagates_without_verifying_normal_reap
test_unknown_residual_source_propagates_through_terminate
test_evidence_forced_stop_propagates_unknown_residual_to_sidecar
test_transient_unknown_residual_requires_later_exact_zero
test_setsid_escape_is_not_claimed_as_contained
```

## 波及

共有 helper は author 前の `b7f970dfa` と一致し、その基点からの `git diff` では `_run_launcher_subprocess` の変更 hunk が消えています。HEAD 比較には復元の削除差分が残ります。

他 mode・他 test の実装や期待値に変更なし。production 差分ゼロ。禁止された Git 操作は実行していません。

## 総括

実装済み：fix1 全項目。焦点17本 passed。  
未実走：全走・変異再走・timeout／rc 97 等の故障注入。  
未着手：なし（本依頼の修正範囲）。