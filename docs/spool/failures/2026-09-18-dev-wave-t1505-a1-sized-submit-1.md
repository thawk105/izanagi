---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t1505-a1-sized-submit
seq: 1
---

## 再発

### F1

- **再発: 2026-09-18** ([T-1505] A-1 sized 本走投入 wave、near miss)。親が handoff へ書いた JST 時刻 3 件 (06:33 / 06:35 / 06:37) が実測でなく推定で、直後の `date` は 06:29:42 だった (実時刻より先へ進んでいた)。原因は wave 冒頭の `date` 1 回に体感の経過を足したこと。記録 commit・insight へ入る前に `stat` の mtime で 06:24:21 / 06:28:23 / 06:29:14 へ置き換えた。恒久対応は変更なし — 時刻を書く 1 回ごとに `date` か mtime を採る。
