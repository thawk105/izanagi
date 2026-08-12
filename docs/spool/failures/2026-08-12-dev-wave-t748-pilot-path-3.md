---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t748-pilot-path
seq: 3
---

## 再発

### F24

- **再発: 2026-08-12** — **偽 green を返したのが通知ではなく待ち手自身**という新しい形。
  段 6 fix の待ち手 (`tools/dev_wave_wait.py producer`) を背景で起動したところ、
  **`.done` も成果物も存在せず producer (pid 1559257) も生存したまま rc=0 で返り、
  stdout は空**だった。張り直しても同じ形で即座に返った。
  同じ argv を**前景で走らせると `error: stage=producer-timeout rc=70` を正しく返す**ことを実測しており、
  背景実行時だけ無音で終わる。**恒久対応は既存の `DW-O01` で足りる** —
  完了判定を成果物実在・`.done` の exit code・producer の死の 3 点照合に限る規律が、
  待ち手の rc が偽である場合にも例外なく効いた。本 wave の追加事実は
  **「待ち手の rc も判定に使えない」**点で、以後の待ちは `.done` 出現と producer 死を
  直接見る条件ループへ切り替えた。
