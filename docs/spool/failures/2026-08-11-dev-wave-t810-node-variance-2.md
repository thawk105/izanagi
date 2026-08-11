---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t810-node-variance
seq: 2
---

## 再発

### F57

- **再発: 2026-08-11 ([T-810] 受入全走)** — bnode010 の全走 (request `903811.nqsv`、543 秒) で
  `test_codex_worker_launch.py::test_check_receipt_rejects_unknown_and_duplicate_fields` が 1 件落ちた。
  述語は既載と同じ 2 本 (`failed_predicates=["process_group_residual","termination_verified"]`) で、
  `codex_exit_code=0` / `validator_rc=0` / `evidence_status='complete'` /
  `metering_status='complete'` はすべて正常、`wall_clock_s=0.132` も上限 3 秒に対し十分小さい。
  同 node の単独再走 (計算ノードへ dispatch) は **1 passed / 3.27 秒 / rc=0** で再現しない。
  本 wave の差分は **docs のみ**で launcher 実装にも同 test file にも到達しえず、
  `DW-O18` により帰属しない。**新しい情報が 2 つある。**
  (1) `loadavg=(17.42, 4.83, 4.03)` で発火した。既載の 1 分平均は 15.05 / 12.67 / 12.92 であり、
  **17 台は既載の最大を上回る**。同時に 5 分平均 4.83・15 分平均 4.03 も既載 (3.57/3.24/3.66 と
  1.18/1.68/1.90) より高く、**瞬間負荷だけでなく持続負荷が高い状態での発火**は本件が初出である。
  発火時は並行 wave の計算ノード job が 3 本走っていた。
  (2) **同一 file の 4 つ目の node** である。既載は `test_late_rollout_writer_does_not_change_sealed_receipt`、
  `test_all_repo_policy_reasoning_values_are_accepted[xhigh]`、
  `test_fake_stdout_matches_observed_cli_event_shape` で、述語系の失敗が移動し続けることをさらに裏付ける。
  恒久対応は [T-553] のままで本 wave では変えない。
