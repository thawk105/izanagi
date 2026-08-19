---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t470-accepted-consumer
seq: 3
---

## 再発

### F365

- **再発: 2026-08-20** — `dev-wave-t470-accepted-consumer` wave で、main 取り込み merge
  (`0e07ad03`) が main 側 (workload-policy-hint-impl wave) と本 wave の両方が
  `orchestrator/campaign/layer3_report.py`/`orchestrator/tests/test_layer3_report.py` を
  実装面として変更していたことにより (競合なしの自動 merge、`git merge` は
  "Automatic merge went well")、`tools/check_ai_provenance.py` の combined-path 判定
  (両親からの積集合が非空) で新規違反として検出された。F365 の恒久対応
  (`preclaim-history-provenance`: claim 前に無条件で全史監査) が意図どおり機能し、
  lease を一切消費せず (`claimed_main: null`) `tools/dev_wave_wait.py acceptance` が
  rc=70・25秒で早期に land 不能を検出した (queue 待ち行列への影響ゼロ)。
  checker ソース中の「(ユーザー選択: known-violation 登録)」の指示どおり、
  この新規違反の台帳登録可否は AI 単独で判断せずユーザーへ返した。
