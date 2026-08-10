---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t8b-restart-integration
seq: 1
---

## 再発

### F57

- **再発: 2026-08-11 (8b 再開統合 wave の変異 baseline)。** 変異 harness の baseline (48 worker 全走、
  523.38 秒) で `test_codex_worker_launch.py::test_all_repo_policy_reasoning_values_are_accepted[xhigh]`
  が 1 件落ち、harness は production write 前に fail-closed で中止した (rc=2、**1 failed**)。
  同 file の単独再走は **77 passed / 6.00 秒 / rc=0** で再現せず、2 回目の baseline は
  **PASSED / rc=0 / 533.56 秒** だった。本 wave の差分は `s8b_holdout_freeze.py` と同 test file だけで
  launcher 実装へ到達しえず、`DW-O18` により帰属しない。
  **新しい情報が 2 つある。** (1) 2026-08-10 の既載再発は `loadavg=(15.05, 3.57, 1.18)` だったが、
  本件は `loadavg=(12.67, 3.24, 1.68)` で同じ述語 2 本
  (`failed_predicates=["process_group_residual","termination_verified"]`) が不成立になった。
  **1 分平均 15 台でなく 12 台でも発火する**ことを示す。(2) 既載は
  `test_late_rollout_writer_does_not_change_sealed_receipt` で、本件は**同一 file の別 node** である。
  述語側の不成立が異なる node へ移動した初の対照であり、F57 の題が言う「失敗 node が移動する」
  性質が述語系の失敗でも成り立つことを裏付ける
- **再発: 2026-08-11 (同 wave の変異 MU-1、別 test file)。** 変異 MU-1 の走行で期待 node
  (`test_verify_cli_active_receipt_hash_mismatch_is_immediate_red`) が正しく落ちた一方、
  `test_campaign.py::test_pipeline_stale_screening_falls_back_to_verify_first_and_records_trace`
  が同時に落ち、harness の完全一致判定が **MISMATCH** を返した (期待は KILLED)。
  同 test file は `s8b_holdout_freeze` を 1 箇所も参照せず、MU-1 の変異は構造的に到達しえない。
  単独再走は **1 passed / 2.60 秒 / rc=0** で再現しない。
  **新しい情報は、フレークが変異 matrix の判定へ直接漏れること**である。
  `DW-M03` の kill 判定は失敗 node 集合の完全一致で行うため、無関係なフレークが 1 件混ざるだけで
  正しく kill された変異が MISMATCH に化ける。`DW-M02` に従い初回結果を消さず erratum として残し、
  実質 KILLED として扱った。恒久対応は [T-553] のままで本 wave では変えない
