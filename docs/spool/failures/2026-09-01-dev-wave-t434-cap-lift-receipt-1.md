---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t434-cap-lift-receipt
seq: 1
---

## 再発

### F165

- **再発: 2026-09-01** — [T-434] の段 1 brief で「D121 の前提条件 P1〜P9 の独立評価器は repo に
  1 件も実在しない」と書いた。根拠は「`D121` を参照する `orchestrator/` 配下の実装が 0 件」という
  自分の grep である。実際には P1 は D160 が充足を記録しており、`reflux_formal_consumer.py` に
  条件評価の実装があって `FormalReasonCode.P6_UNAVAILABLE` で明示停止する。参照検索の実測
  (「`D121` の文字列が 0 件」= 正しい) を機構レベルの主張 (「評価器が 0 件」= 誤り) へ一般化した、
  F165 と同一の型である。段 3 の敵対レンズ 2 本が独立に指摘し、親が現物で追認した。
  実害なし。解除条件を「評価器 9 本の新設」と誤認したまま裁定へ進む手前で止まった。
  恒久対応は F165 と同じ `DW-S03` の義務であり、本件も同 gate が実際に発火した事例である。
