---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-acceptance-pyc-warm
seq: 3
---

## 再発

### F1031

- **再発: 2026-09-30 (near miss、md_7 acceptance-pyc-warm wave)** — 変異用の独立 clone を作る script の引数に、統合 commit の 40 hex SHA を `git rev-parse` の出力から写さず、短縮形 (`f4920ddb3`) の後ろを推測で補完して渡した。`git update-ref` が nonexistent object で拒否し (clone 作成は rc 6 で停止)、`rev-parse` の出力で別名の clone を作り直した。同日の md_6 (acceptance-shard0-load) wave も worklog に同型を記録しており、変異元 clone の作成で繰り返し起きている。恒久対応は既存どおり (SHA は `rev-parse` の出力を逐語で写すか短縮形のまま渡す)。
