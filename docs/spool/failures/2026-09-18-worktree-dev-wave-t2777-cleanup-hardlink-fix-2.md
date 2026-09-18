---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: worktree-dev-wave-t2777-cleanup-hardlink-fix
seq: 2
---

## supersede 追記

- F1026 **supersede: 2026-09-18** — 恒久対応は [T-2777] で実装した (commit 94715928d + fbd8c7038): `_read_admin_file` は admin dir 相対 path が object の名前形 (`modules/…/objects/<2hex>/<38|62hex>`、`modules/…/objects/pack/pack-<40|64hex>.<ext>`、`modules` と末尾 3 component の間に `refs`/`logs` を含まない) の regular file に限り nlink>1 を許容し、registry file の拒否は不変。正例・負例 6・race 2 を変異登録 (M1〜M5 KILLED、等価 M0 SURVIVED)。名前形外の補助 file (`objects/info/*`、`multi-pack-index` 等) の hardlink は現行どおり rc=20。本 wave の段 9 の rc は次 wave の worklog へ。一次資料 `output/insights/2026-09-18/t2777-cleanup-hardlink-fix/README.md`。
