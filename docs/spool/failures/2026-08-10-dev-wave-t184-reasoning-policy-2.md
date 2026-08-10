---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t184-reasoning-policy
seq: 2
---

## 再発

### F57

- **再発: 2026-08-10 ([T-184] 受入全走)。** bnode021 の全走 (7,864 件、request `898552.nqsv`、
  1316.27 秒) で `test_codex_worker_launch.py::test_late_rollout_writer_does_not_change_sealed_receipt`
  が 1 件落ちた (1 failed / 7843 passed / 20 skipped)。同一 checkout の単独再走は
  1 passed / 3.35 秒 で再現しない。当該 wave の差分は **docs のみ**で launcher 実装・同 test file へ
  到達しえず、`DW-O18` により帰属しない。**新しい情報が 2 つある。** (1) 失敗の様態が従来の
  `assert 1 == 0` / returncode 不一致ではなく、`failed_predicates=["process_group_residual",
  "termination_verified"]` という**終了検証側の述語 2 本の不成立**だった
  (`codex_exit_code=0` / `validator_rc=0` / `evidence_status='complete'` /
  `metering_status='complete'` はすべて正常で、`wall_clock_s=0.0994` は上限 3 秒に対し十分小さい)。
  (2) 失敗時の `runtime_context` に `loadavg=(15.05, 3.57, 1.18)` が記録されており、
  **1 分平均だけが突出した瞬間負荷**の下で発火している。これは「wall 上限の超過」ではなく
  「高負荷下で子 process group の終了確認が期限内に観測できない」機序を示唆する。
  従来の再発記録は returncode 系に偏っており、述語側の不成立は本件が初出である
