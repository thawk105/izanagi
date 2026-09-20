---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2810-g1-launch-validation
seq: 3
---

## 再発

### F100

- **再発: 2026-09-20** (near miss、実害なし) — 凍結 v2 g1 の launch validator 修復 wave の親が、段 5 実装子の進捗確認で `cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t2810-unit-impl 2>/dev/null && echo …` (読み取りだけ) を Bash に含め、harness の追跡 cwd が author の子 worktree へ移った。`EnterWorktree(path=<自分の wave worktree>)` で即復帰 (HEAD・clean 不変)。書き込みは発生していない。同型: 他 worktree の file を見るときは絶対 path で `ls` / `cat` し、`cd` を前置しない (memory `worktree-discipline` の「cwd の罠」、本台帳の 2026-09-18 3 件と同じ手順で復帰)。
