---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2406-s4loop-gflags
seq: 3
---

## 再発

### F873

- **再発: 2026-09-08** — 実装単位が 1 つの隔離 wave で、恒久対応 (wave worktree で直接走らせる) を適用せず `.codex/worktrees/` に author / fix 用の別 worktree を作り、dry-run を `cd <別 worktree> && …` で打って永続 shell の cwd を移し、以後の Bash が全拒否された。`EnterWorktree(path=自 worktree)` で復旧し実害なし。原因は起動前に「実装単位は 2 つ以上か」を数える再発検知を踏まなかったこと。
