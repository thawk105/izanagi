段 6 fix を指定の 2 ファイルだけに反映しました。判定は静的確認上のものです。

### 所見ごとの対応表

| 所見 | 判定 | 対応 |
|---|---|---|
| F1 | closed | bare `State` を含む統合 scanner、対象 ID 前の state 拒否、重複・矛盾拒否を実装。[dispatch_compute.py:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:266)、[test_pegasus_dispatch_compute.py:934](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:934) |
| F2 | closed | receipt 内 mutable record、helper 前 claim、独立 once-only latch、qdel 結果の先行固定を実装。3 signal seam を追加。[dispatch_compute.py:977](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:977)、[dispatch_compute.py:1385](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1385)、[test_pegasus_dispatch_compute.py:1212](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1212) |
| F3 | closed | qdel 前 clock 失敗を `gate-exception` 化、sleep を残予算で制限、qdel 後失敗は elapsed null と例外を保存。[dispatch_compute.py:1017](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1017)、[test_pegasus_dispatch_compute.py:1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1088) |
| F4 | closed | rc=153 でも対象 ID＋QUE stdout を持つ応答を上限まで transient retry し、qdel しないテストを追加。[test_pegasus_dispatch_compute.py:1028](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1028) |
| F5 | closed | `Current State = Queued/Held/Staging` 単独の正例を command 完全一致で追加。[test_pegasus_dispatch_compute.py:863](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:863) |
| F6 | closed | qdel 非ゼロ・例外の両経路で gate qstat 1 回、qdel 1 回を含む完全な scheduler command 列を固定。[test_pegasus_dispatch_compute.py:1819](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1819) |
| F7 | closed | request ID 不明時の旧 `qdel.reason` を復元。成功時の既存 4 field と `job_may_remain=false` を固定。[dispatch_compute.py:1100](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1100)、[test_pegasus_dispatch_compute.py:824](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:824)、[test_pegasus_dispatch_compute.py:1920](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1920) |
| F8 | closed | 指定 6 テストすべてに総 qstat 回数または gate attempt 件数を追加。[test_pegasus_dispatch_compute.py:681](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:681)、[test_pegasus_dispatch_compute.py:1143](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1143)、[test_pegasus_dispatch_compute.py:1819](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1819) |
| F9 | closed | `tools/`・`orchestrator/` を走査し、alias、class method、別 module import、属性呼出しを検出する scanner と自己テストを追加。[test_pegasus_dispatch_compute.py:1277](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1277)、[test_pegasus_dispatch_compute.py:1359](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1359) |

### 実測

テスト、py_compile、変異、その他の実行検査は行っていません。緑は主張しません。親はまず次を実行してください。

- `python3 -m py_compile tools/pegasus/dispatch_compute.py`
- `orchestrator/tests/test_pegasus_dispatch_compute.py` 全体
- 焦点 nodeid:
  - `::test_target_bound_gate_rejects_malformed_or_conflicting_state`
  - `::test_fresh_qstat_gate_accepts_current_state_only_snapshots`
  - `::test_nonzero_qstat_with_target_que_stdout_never_bypasses_transient_gate`
  - `::test_fresh_qstat_gate_clock_failure_before_qdel_is_gate_exception`
  - `::test_fresh_qstat_gate_clips_transient_sleep_to_remaining_budget`
  - `::test_qdel_result_is_not_overwritten_by_post_qdel_gate_clock_exception`
  - `::test_cleanup_signal_after_qdel_is_once_only_and_preserves_first_result`
  - `::test_allowed_qdel_failure_records_job_may_remain_and_warns`
  - `::test_request_id_discovery_failure_skips_gate_commands_and_warns`
  - `::test_best_effort_qdel_reference_scanner_covers_bypass_shapes`
  - `::test_best_effort_qdel_production_caller_is_only_fresh_gate`

### 所有外への波及可能性

- `tools/run_tests.py` と `tools/check_ai_provenance.py` は引き続き dispatch の整数 rc を消費する。
- receipt consumer には `cleanup_elapsed_s=null` と `cleanup_elapsed_exception` が追加され得る。
- cleanup claim 後の SIGINT/SIGTERM は receipt 永続化を優先し、再 qdel を起動しない。
- caller meta-test は今後 `tools/`・`orchestrator/` の Python から低水準 qdel を直接 import/callすると赤になる。
- 監視用 `_scheduler_state()`、`state_history`、task enum、docs/output は変更していない。
- commit、index、branch 操作は行っていない。

### 受理集合の変化

前段実装から、次だけを fail-closed 側へ変更しました。

- 対象 block 内の bare `State` と他 state field の矛盾を拒否。
- 対象 ID より前に認識可能な state がある出力を拒否。
- qdel 前の clock 取得不能を拒否。
- transient sleep を cleanup 残予算以内に制限。
- cleanup 中の signal による二重 qdel を拒否。

`QUE/HLD/STG`、既存 bare abbreviation、`Current State` 単独形、整合する複数 field の受理は維持しています。

## 総括

F1〜F9 は静的確認上すべて closed です。`dev-wave` の段 6 worker 契約に従い、指定 2 ファイル以外、docs/output、commit には触れず、実測は親へ残しました。