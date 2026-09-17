---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2737-ss2pl-gate-controls
seq: 3
---

## 再発

### F100

- **再発: 2026-09-18** (near miss、実害なし) — 隔離 worktree の session が Bash で `cd <Codex author の probe worktree> && grep …` (読み取りだけ) を実行したところ、harness の追跡 cwd がその worktree へ移り、以後の全 command (`pwd` すら) を隔離 guard が「共有 checkout で実行しようとした」として拒否した。`EnterWorktree --path <自分の wave worktree>` で復帰。書き込みは発生していない。同型: read-only の調査で `cd <他 checkout> &&` を前置する癖が、guard の cwd 追跡と衝突する。他 worktree の file は絶対 path で読み、`cd` を前置しない (memory `worktree-discipline` の「cwd の罠」)。
