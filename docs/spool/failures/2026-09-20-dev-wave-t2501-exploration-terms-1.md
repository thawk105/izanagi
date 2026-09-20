---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2501-exploration-terms
seq: 1
---

## 再発

### F1

- **再発: 2026-09-20 (near miss)** — [T-2501] wave (docs のみ) の親が、専用 handoff の段 1 brief と段 4 裁定の見出しに書いた JST 時刻
  (21:05 / 21:12) を `date` で実測せず推定で書いた。実際はどちらも commit 1 (`git log --format=%ci` で 21:04:51) より前で、brief は開始 gate
  (`startup-gate.log` の mtime 20:53:36) の後である。段 7 で commit 日時と mtime を採ったときに気づいた。逐語 (insight `verbatim/brief.md` /
  `verbatim/adjudication.md`) は改変せず、insight README §2 に訂正を書いた。成果物 (runbook / glossary) への影響は無い。
  原因は 2026-09-18 の再発と同型 — wave 冒頭の `date` 1 回に体感の経過を足した。恒久対応は変更なし — 時刻を書く 1 回ごとに `date` か mtime を採る。
