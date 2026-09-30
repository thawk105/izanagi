---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-10-01
wave: worktree-dev-wave-t2865-r2-replay
seq: 2
---

## 再発

### F26

- **再発: 2026-10-01** — 作成側の再発 (2026-09-02 の kill 形)。[T-2865] の R2 再測定で submit checkout を repo 外の job dir に 1 本ずつ直列に作る script (`git worktree add --detach` → submodule 初期化 → `git worktree lock` → hydrate) を背景 command で回したところ、4 本目 (`trees/c3r2`) の `git worktree add` が 03:26 に作業ツリーの展開まで進んだまま戻らず、背景 command の 30 分上限で kill された (前の 3 本は各 2 分前後で完了)。その後は `.git/worktrees/c3r2` が無く `git worktree list` に現れず、dir の中身は 04:02 以後に減り続けた。管理 dir と中身を消した主体 (中断された add 自身の後始末か別の主体か) は確かめていない。lock を add の後に掛ける順序だと、add が戻らない間は無防備な中途状態が残る。作り直しは `git worktree add --lock --reason ...` で追加と lock を同時に行い、別名 (`trees/c3r2b`) で 2 分で完了した。孤児 dir には触れていない。記録 `output/insights/2026-10-01/t2865-r2-replay/README.md` §4。
