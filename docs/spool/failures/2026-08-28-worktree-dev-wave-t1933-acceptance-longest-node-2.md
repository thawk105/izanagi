---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: worktree-dev-wave-t1933-acceptance-longest-node
seq: 2
---

## 再発

### F606

- **再発: 2026-08-28** — T-1934の開始handoffは、約40分前から存在してlockedだったT-1933専用worktreeとrepo外job directoryを「専用worktree/branch/processは無く、ownerなし」と記録した。両waveとも実装面0 byteで対象2 test fileの直接重複はなく実害は無かったが、段1の稼働wave inventoryが既存ownerを落としたnear missである。T-1933再開時はworktree list、repo外handoff/job directory、process、未commit差分を再走査して訂正した。F606の恒久対応がこの走査面を既に要求するためreferenceは変更しない。
