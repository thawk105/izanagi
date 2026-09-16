---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2502-k2-coder-role-conditional
seq: 2
---

## 再発

### F672

- **再発: 2026-09-17** — [T-2502] wave の land 2 巡目 (02:11 JST、1 巡目 rc=10 で main fa24e6ea8 を固定 SHA merge した
  直後) が `rc=31 status=fold-gate-failed` / `registered worktree path cannot be resolved: [Errno 4] Interrupted system
  call: '<共有 repo>/.codex/worktrees/t1994-fix5'` (別 wave の登録 path) で止まった。`release_safe=true` /
  `retryable_same_request=false`、`main_before == main_after == fa24e6ea8`。受入 1 (child-green、24389 passed / 67 skipped) を
  捨て、既存 F672 の復旧どおり同じ tip に本 fragment を積んで受入を取り直し、新しい request で land を再試行する
  (結果は worklog 側に書く)。他 wave の登録は触っていない。
