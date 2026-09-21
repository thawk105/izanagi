---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-t2825-ledger-refresh-ab
seq: 2
---

## 再発

### F633

- **再発: 2026-09-21** — [T-2825] の A/B 測定走 03-B (固定 2 tree の直接投入、受入形) で `test_t810_coordinator.py` の prepare_group 系 3 node が `cannot read worktree registration: file is absent` (`.git/worktrees/diag-login-check-wall/gitdir`、別 session が走行中に撤去) で赤。本 wave の差分 (台帳 1 file) から到達しないこと (同 test file は台帳を参照しない) と単独再走 3 passed (request 14912.nqsv) で infra に分類し、事前登録どおり走だけを無効化して対を同順序で取り直した。測定系列の赤は親の本文分類が要るので、系列は 1 走分 (約 26 分) と分類の手間を失った。

### F953

- **再発: 2026-09-21** — [T-2825] 段 6 の review launcher を段 3 consult launcher から写して `--reasoning medium` を残し、review 2 本とも `--reasoning は --stage review/focus/author/fix では指定できない` で rc=2 (子は 1 call も走らず)。author / consult の launcher には投入前に `--dry-run` を打っていたが、review の launcher では省いた。以後の fix / focus / 台帳 fix の launcher は全部 `--dry-run` rc=0 を確かめてから投入した。
