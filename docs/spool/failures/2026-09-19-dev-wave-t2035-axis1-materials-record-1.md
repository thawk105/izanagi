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
  **同 wave で連続 2 回 (5 例目、23:09 JST):** 受入 2 (child-green、tested tip `ec54716d3`、main `8fd1eecf9` を前方 merge した
  landing tip `b81d16ddf`) の land 2 巡目も同型で、path は別の他 wave (`<job dir>/dev-wave-verify-phase-adopted-backoff/submit-tree-a4`)。
  2 回とも `window_elapsed_s` ≈ 225 秒、`fold_gate_*_families` は両方空、直後の読取専用 `resolve(strict=True)` は 2 path とも即時成功。
  機序の候補 (未検証): `_FoldGateOuterWatchdog` が `setitimer(ITIMER_REAL, 0.1, 0.1)` で SIGALRM を 0.1 秒ごとに投げるため、登録
  worktree (68 本) を `resolve(strict=True)` する間に共有 FS の遅い syscall が中断され、PEP 475 の自動再試行外の呼び出しが `EINTR` を
  返す。受入 2 も捨て、受入 3 を取り直す。
