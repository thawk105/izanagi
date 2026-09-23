---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-23
wave: worktree-dev-wave-paper-story-20260923
seq: 2
---

## 再発

### F25

- **再発: 2026-09-23 (near-miss、論文ストーリー 2026-09-23 版の wave)** — 親が段 6 の fix commit を `git commit -m <件名> -m <AI-Agent 行> -m <Co-Authored-By 行>` の 3 分割で作り、AI-Agent 行と Co-Authored-By 行が別段落になって AI-Agent が trailer と認識されず、全史 provenance 監査が新規違反 1 件 (rc=1) を出した。`--message-file` の事前検査を `-m` 分割の commit では通していなかった。未共有のうちに soft reset で記録 commit と 1 つにまとめて作り直した (内容は同じ)。以後の commit は Write で作った message file を `--message-file` で検査してから `commit -F` にした (DW-O17 の既存手順どおり)。
