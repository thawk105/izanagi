---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-03
wave: dev-wave-t313-read-budget
seq: 2
---

## 再発

### F50

- **再発: 2026-08-03** — [T-313] wave の立ち上げで、専用 handoff を背景 job harness の既定
  (`$CLAUDE_JOB_DIR/tmp` = home 配下の `~/.claude/jobs/<id>/tmp`) に作り、ユーザーに止められた
  (near-miss、実害なし)。前回 (2026-07-29) は worktree 内、今回は home 配下で、**置き場を
  間違える型は同じ**である。原因は `DW-O20` の「専用handoffはworktree外（背景jobはjob tmp）」
  という文言が、要件 (worktree の外) ではなく harness 既定の実体 (home 配下) を指しており、
  Pegasus の「home に不要物を置かない」規律 (runbook §6 の領域分担) と衝突したこと。
  repo 内 `.claude/jobs/` への退避も worktree 隔離ガードが Write を拒否するため使えず、
  最終的に repo 外の `/work` 配下へ置いた。
  恒久対応 = `DW-O20` の当該語を byte 中立で「背景jobはrepo外」へ是正 (本 wave の段 8) と、
  auto-memory `pegasus-keep-home-clean`。
