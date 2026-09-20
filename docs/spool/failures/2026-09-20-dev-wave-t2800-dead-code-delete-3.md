---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2800-dead-code-delete
seq: 3
---

## 再発

### F359

- **再発: 2026-09-20** — 削除 wave の親が author prompt に `git rm` を指示し、子は `.git/worktrees/<unit>/index.lock: Read-only file system` で無変更終了した (約 1 分)。merge に限らず index を書く git 操作はすべて同族。子は作業ツリーの `rm` と file 編集だけを行い、stage は起動器の終端 commit と親の `git apply --index` が担う。
