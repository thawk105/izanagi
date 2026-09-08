---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2101-proposal-binding
seq: 2
---

## 再発

### F185

- **再発: 2026-09-09** — 変異 spec の `timeout_seconds` を 300 秒に置いたが、その時間帯の
  queue 待ちが実測 8 分 (03:14 投入 → 03:21:59 開始) で、job が走り始める前に harness 自身の
  per-run timeout が切れて dispatcher を落とし、orphan hold を立てた。**job 自体は走り切っており**
  (`result.json` の `child_rc=1` は期待どおりの mutant 赤)、hold は誤検知だった。
  混雑時の最悪値で取り直し (`1800` 秒、job walltime 3600 秒の内側) 完走した。
  この回は「dispatch 実測の倍数」でも足りず、**queue 待ちの分布そのもので決める**必要があった。
