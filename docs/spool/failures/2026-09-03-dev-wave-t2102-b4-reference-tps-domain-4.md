---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-t2102-b4-reference-tps-domain
seq: 4
---

## supersede 追記

- F34 **supersede: 2026-09-03** — 恒久対応 1 (「docs を含むあらゆる記録 commit の後に repo scan invariant を再走してから wave を閉じる」) は現在**発火しない**。`orchestrator/tests/test_s8b_repo_scan_invariant.py` は growth hold (`hold_axis=tracked_files`、`release_condition=explicit-user-command-only`、2026-08-12 rulings 第 3 束) の下にあり、既定では skip される。本 wave が記録 commit 後に指示どおり再走したところ `1 skipped` で、走査は 1 file も見ていない。指示は形式上満たせるが何も閉じない。**本 wave は hold を迂回していない。** 代わりに同じ権威実装 `orchestrator/campaign/s8b_holdout_freeze.search_repository` の `files` 注入 API へ、変更した 17 file と positive control が発火する既存 169 file を渡して走査し、rr80 / rr20 の conjunction hit 0 件・positive control 14 hit を確認した。これは全域走の代替として裁定されたものではなく、本 wave 限りの措置である。**恒久対応 1 をどう回復するか (記録 commit だけ hold を解除するか、走査対象を変更 file + 正例対照へ正式に狭めるか) は正しさ防壁の変更なので、`docs/skill-self-improvement.md` の段 8 契約に従い実装せずユーザー裁定へ返す。**
