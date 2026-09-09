---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2354-a5-prune-removal
seq: 3
---

## supersede 追記

- F251 **supersede: 2026-09-09** — 2026-09-07 再発の「対応は裁定へ返した」は D1700 として裁定され、A-5 job 本体からの共有 gitdir prune 撤去として着地した ([T-2354])。job 本体の掃除は自 path の `worktree remove --force` だけになり、remove 失敗時は残置 path を receipt へ明示する。
- F902 **supersede: 2026-09-09** — 「main 側の余裕は 1 node 未満」は 2026-09-09 時点では解消している。[T-2354] が test node を 2 件足した状態でも被覆 gate は登録前から緑で、`test_acceptance_schedule_order.py` は 79 passed だった。登録は F902 の恒久対応どおり正本 producer の `--add-only` で行った。
