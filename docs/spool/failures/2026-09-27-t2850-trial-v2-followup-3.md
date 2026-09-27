---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-27
wave: t2850-trial-v2-followup
seq: 3
---

## 再発

### F100

- **再発: 2026-09-27** (near miss、実害なし) — [T-2850] 試走 v2 後段 wave の親が、repo 外の glue の差分を読むために Bash で `cd <Codex author の子 worktree の scratch> && diff …` (読み取りだけ) を実行し、harness の追跡 cwd がその子 worktree へ移って以後の command が拒否された。`EnterWorktree(path=<自分の wave worktree>)` で即復帰 (HEAD・clean 不変)。書き込みは発生していない。同型: 他 worktree の file は絶対 path で読み `cd` を前置しない。どうしても `cd` が要る操作は job dir の `.sh` に閉じ込める (本 wave の以後の写し出し・pytest はそうした)。
