---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-27
wave: t2850-trial-v2-followup
seq: 3
---

## 再発

### F633

- **再発: 2026-09-27** ([T-2850] 試走 v2 後段 wave の受入 final2 attempt 1、session root `.izanagi-acceptance-shards/664541b207b8da004472b54e961286e7`) — `test_t810_coordinator.py` の prepare_group 系 3 node (`test_prepare_group_accepts_external_root_with_anchor_union`・`..._rejects_self_consistent_foreign_git_identity_before_any_mkdir`・`..._rejects_forged_git_identity_before_any_mkdir`) が `cannot read worktree registration: file is absent` で赤 (受入中の 15:4x〜15:5x に他 wave 2 本が land していた)。本 wave の差分は docs と insight だけで同 test から到達しない。同じ tip `6a2ae3d73` の単独再走 (31432.nqsv) は 45 passed。非帰属として受入を再走した。

### F100

- **再発: 2026-09-27** (near miss、実害なし) — [T-2850] 試走 v2 後段 wave の親が、repo 外の glue の差分を読むために Bash で `cd <Codex author の子 worktree の scratch> && diff …` (読み取りだけ) を実行し、harness の追跡 cwd がその子 worktree へ移って以後の command が拒否された。`EnterWorktree(path=<自分の wave worktree>)` で即復帰 (HEAD・clean 不変)。書き込みは発生していない。同型: 他 worktree の file は絶対 path で読み `cd` を前置しない。どうしても `cd` が要る操作は job dir の `.sh` に閉じ込める (本 wave の以後の写し出し・pytest はそうした)。
