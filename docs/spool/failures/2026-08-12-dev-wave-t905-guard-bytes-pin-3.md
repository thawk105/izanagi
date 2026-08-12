---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t905-guard-bytes-pin
seq: 3
---

## 再発

### F57

- **再発: 2026-08-12** — [T-905] の変異本走で M2 の失敗 node へ
  `test_all_v3_stages_reject_prior_invalid_attempt[author-None]` が 1 件混ざり、
  期待 node の完全一致が崩れて MISMATCH になった (`receipt["attempts"][-1]["accepted"]` が False)。
  M2 は pin 集合から 1 path を外す変異で検査を緩める向きであり、当該 node への因果経路が無い。
  M2 単独再走では期待 6 node と完全一致で KILLED、混入 node は再現せず帰属から外した。
  変異走 (48 worker) で launcher の receipt 系 node が 1 件混ざる形は
  worklog (476) の M3 に続く独立 2 例目である。恒久対応は F57 既載のとおり失敗 artifact 保存による
  原因分離であり、本 wave では変えない。
