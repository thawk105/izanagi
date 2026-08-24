---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-24
wave: dev-wave-t1539-insights-retention
seq: 3
---

## 再発

### F489

- **再発: 2026-08-24** — `test_git_argv_spy_sees_only_allowlisted_cleanup_commands`を現行main・wave・serial単独で実走すると、消滅pid型issueがD705の3 scanすべてで続き`status=indeterminate`/rc22。同file全体では同型7 red/83 passed。T-1539から到達不能な既知赤としてexact fileをcanonical acceptanceだけ一時除外し、修理・再導入を{{T:dev-wave-cleanup-occupancy-churn}}へP1起票した。
