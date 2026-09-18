---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2379-syspath-selfcontained
seq: 2
---

## 再発

### F1

- **再発: 2026-09-18** — [T-2379] wave (branch `dev-wave-t2379-syspath-selfcontained`) の親が、専用 handoff (repo 外) の「最終更新」と
  段 4 の見出しに `date` を叩かず推定した時刻 (11:52 / 11:30) を書いた。直後の `date` 実測は 11:31 で、片方は 20 分以上未来だった。
  worklog・insight へ写す前に気づき、handoff を date 値で訂正し、以後の時刻は `date` と job の Started/Ended Request Time から採った
  (worklog エントリ・insight に誤時刻は入っていない = near miss)。型は 2026-09-17 の再発と同じ「推定で書く」。恒久対応は変更なし
  (memory `timestamps-from-date-or-mtime-not-estimation`。時刻・日付を報告に載せる前に `date` を叩く)。
