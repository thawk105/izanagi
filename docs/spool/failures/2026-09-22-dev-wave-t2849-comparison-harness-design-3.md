---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-22
wave: dev-wave-t2849-comparison-harness-design
seq: 3
---

## 再発

### F1

- **再発: 2026-09-22 (near-miss)** — T-2849 の設計 wave で、親が段 4 裁定の見出し時刻を「10:0x JST」、handoff の段 3 相談の投入時刻を「09:3x JST」と推定で書いた。実際は `date` の 09:29 と、pid file の mtime 09:20:49 / 09:20:54 だった。repo へ入る前 (job dir の段階) に `date` と mtime で直し、insight と worklog fragment には実測の時刻だけを書いた。恒久対応は `DW-S01` の「日時・hash・件数は commit / 成果物 field から取る」と memory `timestamps-from-date-or-mtime-not-estimation` から変更なし (時刻を書く直前に `date` か mtime を取る)。
