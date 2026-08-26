## 総括

実装済み・未実走です。  
latch 側から不正な sleep 下限を削除し、注入 clock の読み取りだけを検証する形へ修正しました。  
既存の性質 assertion、watchdog、Event の条件は変更していません。  
`git diff --check` は通過しました。

## latch 側が poll しないことの静的確認

最初の `qstat -f` は `Permission denied` となり、production の permission 分岐で retry 用 `sleep` より先に抜けます。

cleanup は次の `qstat` で `QUE`、qdel 後に既定の `EXT` を観測するため、ここでも retry sleep はありません。control lock 自体も blocking `flock` であり、poll しません。

一方、注入 clock は `started = clock()` と `submitted_at = clock()` で確実に読まれるため、`read_calls > 0` は成立します。

## 2 test それぞれの観測点と、sleep= / clock= 削除の検出可否

`test_control_lock_serializes_latch_check_through_immediate_visibility`:

- `sleep=` 削除: poll しないため等価変異です。検出対象外であることをコメントへ明記しました。
- `clock=` 削除: `_RecordingClock.read_calls` が 0 のままとなり、`assert first_clock.read_calls > 0` で赤になります。

`test_control_lock_allows_peer_after_pending_hold_is_durably_released`:

- `_Scheduler.states` の `DONE` の添字は 2 です。したがって下限は `poll_interval_s * scheduler.states.index("DONE")`、現在は 10 仮想秒です。
- `sleep=` 削除: `assert clock.sleep_calls` で赤になります。
- `clock=` 削除: recording sleeper は呼ばれますが clock 読み取りは 0 のため、`assert clock.read_calls > 0` で赤になります。
- 既定状態列は `QUE -> RUN -> DONE` なので、両 scheduler とも poll sleep が2回発生します。

## 変更した file と行

[orchestrator/tests/test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-b/orchestrator/tests/test_pegasus_dispatch_compute.py:5455)

変更した nodeid:

`orchestrator/tests/test_pegasus_dispatch_compute.py::test_control_lock_serializes_latch_check_through_immediate_visibility`

成功側 nodeid は静的確認のみで、この巡では変更していません。

## 実走したか

実装済み・未実走です。テストおよび変異 matrix は実行していません。

## 所有外への波及可能性

- production、共有 fixture、他の consumer testへの動作変更はありません。
- 親の変異 spec では、latch 側の `sleep=` 削除を等価変異として扱う必要があります。
- 成功側では引き続き `sleep=` と `clock=` の両削除を検出対象にできます。

## 未完・未確認

親による対象ファイル実走と、成功側の2変異および latch 側の `clock=` 変異の実走確認が未完です。