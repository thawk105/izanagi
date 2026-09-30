---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-md26-vhash-gc-connection-proof
seq: 3
---

## 再発

### F100

- **再発: 2026-09-30** (near miss、実害なし) — VHash md_26 wave の親が、worklog fragment の `base:` を land 先の local main の台帳で取るために Bash で `cd <主 checkout> && python3 tools/spool_fold.py --base-digest …` (読み取りだけ) を実行し、harness の追跡 cwd が主 checkout へ移って以後の Bash が隔離 guard に拒否された。`EnterWorktree(path=<自分の wave worktree>)` で即復帰 (HEAD・clean 不変、書き込みなし)。同型: `spool_fold.py --base-digest` は cwd の台帳を読み、対象 repo を指定する引数が無いので、`docs/spool/worklog/README.md` の「digest は land 先の local main の現物に対して取る」を隔離 session で実行すると `cd` を誘う。主 checkout での lookup は job dir の `.sh` に閉じ込める。
