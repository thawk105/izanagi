指定 2 ファイルだけを編集し、G1〜G4 をすべて対応しました。テスト・py_compile・commit は実行していません。

### G1〜G4 対応表

| 項目 | 状態 | 対応 |
|---|---|---|
| G1 | closed | scanner を既存 parser と同じ `\s*` grammar に統一し、新たに可視化された非 space/tab 行頭は fail-closed。form-feed・vertical-tab・NBSP が既存 parser で認識されることと qdel ゼロを固定。[dispatch_compute.py:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:124)、[test_pegasus_dispatch_compute.py:953](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:953) |
| G2 | closed | claim 後の最初の signal を `pending_cleanup_signal` と `outcome.reason` に記録。qdel latch を維持し、receipt 永続化直後に INFRA 終了へ伝播。テストは登録済み handler を実際に呼び、qdel 1 回・初回結果・signal reason・receipt を同時検査。[dispatch_compute.py:1407](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1407)、[test_pegasus_dispatch_compute.py:1252](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1252) |
| G3 | closed | `request_id=None` を初回 clock より先に処理し、旧 reason、`job_name`、`submission_dir` を保持。初回から例外を投げる clock が呼ばれない複合条件を固定。[dispatch_compute.py:1070](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1070)、[test_pegasus_dispatch_compute.py:2014](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:2014) |
| G4 | closed | `_best_effort_qdel` を末尾属性に持つ `ast.Attribute` 代入を alias として伝播。提示された `dc._best_effort_qdel` 形を自己テストへ追加。[test_pegasus_dispatch_compute.py:1344](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1344)、[test_pegasus_dispatch_compute.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1404) |

### 親が実測すべき nodeid

以下は未実行です。緑は主張しません。

- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_target_bound_gate_counts_state_whitespace_recognized_by_existing_parser`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_cleanup_signal_after_qdel_is_once_only_and_preserves_first_result`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_request_id_unavailable_precedes_initial_cleanup_clock_failure`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_best_effort_qdel_reference_scanner_covers_bypass_shapes`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_best_effort_qdel_production_caller_is_only_fresh_gate`

その後、同テストファイル全体を `tools/run_tests.py` 経由で実測してください。

### 受理集合の差

前回 fix から受理集合は広げていません。

- 許可状態は引き続き QUE/HLD、STG→QUE の既存正規化のみです。
- 非 space/tab 空白付き QUE 単独形は新規受理せず UNKNOWN へ倒します。
- 差分は、非標準空白で隠された RUN と QUE の矛盾形を拒否する、指示どおりの縮小だけです。
- G2〜G4 は scheduler 状態の受理集合を変更しません。

### 所有外への静的な波及可能性

- `tools/run_tests.py` と `tools/check_ai_provenance.py` の dispatch receipt で、claim 後 signal が `outcome.reason` に現れます。
- receipt schema は v2 のままです。新しい schema field は追加していません。
- 監視用 `_scheduler_state()`、`state_history`、task enum、qsub/discovery の受理集合は変更していません。
- G4 scanner は `tools/`・`orchestrator/` の caller 閉包検査だけに影響します。
- docs・output・runbook は編集していません。commit・git による変更操作も行っていません。

## 総括

G1〜G4 は静的実装上 closed です。編集は指定された実装・テストの 2 ファイルだけで、実行検査は権限契約どおり親へ残しています。