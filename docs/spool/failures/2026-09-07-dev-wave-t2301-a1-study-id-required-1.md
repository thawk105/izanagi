---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2301-a1-study-id-required
seq: 1
---

## 再発

### F672

- **再発: 2026-09-07** — 同じ `registered worktree path cannot be resolved` が `[Errno 2] No such file or directory: '/scr'` で出た。path は a5 second boot の bench job 2 本 (979578/979579) が計算ノードのローカル scratch `/scr/<jobid>-a5-second-boot-<workload>/job-repo` に `git worktree add --detach` した登録で、login node からは job が走る間 (上限 7200 秒) ずっと解決できない (`git worktree list` は `prunable` と表示する)。job は EXIT trap で `worktree remove --force` + `prune` するので job 終了で消えるが、その間は repo 全体の land が `rc=31` / `retryable_same_request=false` で塞がる。一時エラーの種類が EINTR から「別ホストにしか存在しない path」へ広がっただけで、機序 (全登録 path の strict 解決 + OSError 一律非再試行) は同じ。本 wave は受入 (child-green、20834 passed) を捨てて job 終了後に取り直した。running 中の job の登録を login 側から prune してはいけない (job 側の git が壊れる)。
