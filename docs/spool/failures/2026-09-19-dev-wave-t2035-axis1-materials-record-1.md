---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-19
wave: dev-wave-t2035-axis1-materials-record
seq: 1
---

## 再発

### F672

- **再発: 2026-09-19** — [T-2035] wave の land 1 巡目 (22:40 JST 頃、受入 1 = child-green、25,323 passed / 69 skipped、
  tested main `657e1e5a7` / tested tip `ca3625c8b`) が `rc=31 status=fold-gate-failed` / `registered worktree path cannot be
  resolved: [Errno 4] Interrupted system call: '<共有 repo>/.claude/worktrees/dev-wave-t2786-recovery'` (別 wave の登録 path) で
  止まった。`release_safe=true` / `retryable_same_request=false`、`main_before == main_after == 657e1e5a7`。既存 F672 の復旧どおり
  受入 1 を捨て、同じ tip に本 fragment を積んで受入を取り直し、新しい request で land を再試行する。他 wave の登録は触っていない。
  恒久対応 (EINTR を `_FoldGateInfrastructureFailure` 側へ分類する) は依然として未実施・裁定待ちのまま (4 例目)。
