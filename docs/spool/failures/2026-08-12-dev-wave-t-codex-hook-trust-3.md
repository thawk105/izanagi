---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t-codex-hook-trust
seq: 3
---

## 再発

### F57

- **再発: 2026-08-12 (codex hook trust wave の変異 baseline 2 連続)** — 変異 harness の baseline が
  2 走続けて落ち、いずれも production write 前に fail-closed で中止した (rc=2)。
  1 走目は `test_codex_worker_launch.py::test_check_receipt_rejects_impossible_truth_table`、
  2 走目は同 file の `test_delayed_thread_and_rollout_are_read_from_byte_zero` で、
  **失敗 node は既載どおり移動した**。述語は既載と同じ 2 本
  (`failed_predicates=["process_group_residual","termination_verified"]`) で、
  `codex_exit_code=0` / `validator_rc=0` / `evidence_status='complete'` /
  `metering_status='complete'` はすべて正常、`wall_clock_s` も上限 3 秒に対し十分小さい
  (0.168 秒 / 同系)。同 tip の単独再走は **143 passed / 6.33 秒 / rc=0** で再現しない。
  **新しい情報が 2 つある。** (1) 既載の再発はいずれも `loadavg` の 1 分平均が 12〜15 台で
  発火していたが、本件は **1 走目 `loadavg=(0.80, 0.17, 0.16)`、2 走目 `loadavg=(0.65, 2.10, 3.70)`**
  と、**1 分平均が 1 未満の低負荷で 2 回とも発火した**。「瞬間高負荷でだけ出る」という
  既載の示唆は成り立たない。(2) 既載の再発はすべて差分が launcher 実装へ到達しない wave
  (docs のみ等) だったが、本件の差分は `codex_worker_launch.py` の `_attempt_loop` に
  起動前検証を足しており、**到達しうる wave での初の発火**である。ただし当該差分は `Popen` の
  **前**にしか触れておらず、失敗した 2 述語は子 process group の**終了確認**側であって経路が別である。
  同 tip の単独走が緑であること、失敗 node が走ごとに移動すること、
  同じ runner を並列度 `-n 8` へ下げた 3 走目は baseline PASSED で変異 3/3 KILLED になったことから、
  `DW-O18` により本 wave の差分へ帰属しない。
  **運用上の含意**: 変異 harness の baseline は既定の 48 worker では本フレークに当たりやすい。
  並列度を下げた runner で走らせると通った。恒久対応は既載のままで本 wave では変えない
