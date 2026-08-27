---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: worktree-dev-wave-t1905-b10-backoff-shape-codex-resume
seq: 2
---

## 再発

### F510

- **再発: 2026-08-28** — B-10の初回compute jobが `python3 -I -B -m orchestrator...` でrepo rootをimport pathから外し、envelope全通過後にprobe 0 cellで停止した。既に実走済みのA-2は `-B -m` だった。commit `8df4fa25d` でmodule起動だけを修理し、exact job contract testと `-I` 復帰変異1/1 KILLEDで再発検知を固定した。
