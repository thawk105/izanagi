---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2347-scr-worktree-land
seq: 3
---

## supersede 追記

- F851 **supersede: 2026-09-07** — 恒久対応の「未実施」は解消した。案 (a) を {{D:fold-gate-absent-registration}} の形で実装済みで、`_registered_worktree_paths` は `FileNotFoundError` の登録を捨てずに未解決の絶対 path として残し、それ以外の解決失敗は従来どおり fail-closed とする。案として挙がっていた `prunable` marker での除外は実測 3 点により却下した。運用回避 (job が RUN の間は land を投げない) はもう要らない。
