---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t2497-role-sink-status
seq: 3
---

## 再発

### F820

- **再発: 2026-09-14 (3 回目)** — [T-2497] の変異 M5 (`p3_autonomous_workload_trial.py` の
  status 算出を `"complete"` → `"partial"` に反転) は期待 node と完全一致して KILLED になったが、
  赤は追加した test 側の検査ではなく `autonomous_trial_completeness.py:2886` の
  `_check_status_projection` だった。同 gate は producer と同じ述語を独立に再計算して
  `run_trial` の末尾から無条件に呼ばれるため、status リテラルだけを変える変異は
  test へ届く前に内側で死ぬ。**発覚したのは、対にした M5' が MISMATCH になり赤本文を読んだからである。**
  変異 harness は `test_output_tail` を MISMATCH の entry にしか残さないので、
  **期待 node が一致した KILLED は本文を見ないと偽の KILLED と区別できない**
  (F923 と同型で、masking 層だけが違う)。M5 / M5' を取り下げ、
  `_run_pending_critics` へ raise を注入する経路 (M9 / M9') へ再照準して差分を取り直した。
