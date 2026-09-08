---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-next-tasks-command-20260908
seq: 3
---

## 再発

### F100

- **再発: 2026-09-08** — 別 wave の session が主 checkout に cwd を残したまま `git add -A; git commit` を実行し、untracked だった `.codex/worktrees/` 110 本を gitlink として main へ commit した (c12e25078)。今回は near miss でなく実害で、全新規 worktree の submodule 初期化と全 session の land (provenance 全史監査 rc=1) が止まった。前進修正は {{D:c12e25078-forward-fix}}。
