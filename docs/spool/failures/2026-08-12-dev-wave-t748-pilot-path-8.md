---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t748-pilot-path
seq: 8
---

## 再発

### F57

- **再発: 2026-08-12 ([T-748] 受入全走)。** 記録込みの最終 tip での全走で
  `test_codex_worker_launch.py::test_positive_p3_exact_limit_natural_exit_is_accepted` が
  1 件落ちた。述語は既載と同じ 2 本
  (`failed_predicates=["process_group_residual","termination_verified"]`)、
  `launcher_rc=1` / `stop_reason='max_attempts'`。
  **同一 checkout の単独再走は 1 passed / 2.84 秒 / rc=0 で再現しない。**
  本 wave の差分は floor 投入経路・attestation・materializer の cxx 伝播であり、
  launcher 実装にも同 test file にも到達しえないので `DW-O18` により帰属しない。
  本 wave の状況として、**並行 wave が同時に多数走っていた** (受入 lease の待ち行列に
  複数 wave、codex 子も並走) 点が既載の「負荷が高いときに発火する」観察と整合する。
  直前の走行 (同一 wave、記録 commit 前の tip) では **9452 passed / 31 skipped / 0 failed** で
  緑だったので、同一実装で緑・赤の両方を観測している。
