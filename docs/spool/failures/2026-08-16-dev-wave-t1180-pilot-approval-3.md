---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1180-pilot-approval
seq: 3
---

## 再発

### F57

- **再発: 2026-08-16** — 族が `test_mutation_harness.py` へ広がった。[T-1180] 段 9 の受入 1 回目で
  `test_sigterm_handler_stops_child_and_restores_active_mutation` が `gw28` で 1 件だけ落ち、
  SIGTERM 送信前に子が rc=1 で終了して `128 + SIGTERM` を観測できなかった
  (1 failed / 11866 passed / 92 skipped)。同 file の単独実走は 80 passed で再現せず、
  wave の差分 (`tools/pegasus/` の 2 script とその契約テスト) は当該 test へ到達しない。
  既載は `test_codex_worker_launch.py` に集中しており、負荷依存フレークが launcher 族に
  限らないことを示す初の実測である。
