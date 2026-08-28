---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-28
wave: dev-wave-acceptance-fastest
seq: 2
---

## {{D:t080-process-memo-noeffect}}. full K=3 wallを動かさないT-080 process-memo groupingは採らない

**決定:** 同じimmutable baseを使うT-080の6 nodeを同一workerへ寄せる配線は、paired full K=3中央値が10%未満の差なら採用しない。正しく配線され変異が全件KILLEDでも、速くなった証拠の代用にしない。

**理由:**
- fixed tip 3走ずつでpre 244.810秒、post 245.707秒、差+0.37%。D357により変化なしである。
- 焦点6 nodeではcache共有が成立したが、その費用はfull wallのcritical pathの下へ隠れた。
- worker duration総和は下がっても、同じ48-core nodeを同じwall占有し、node秒は仕事量代理にできない。

**却下した選択肢:**
- 焦点走のcache hitだけで採用する — full wallへの因果が無い。
- worker duration総和の低下をmachine cost削減と読む — node-hourは変わらない。
- no-effect配線を残したままKやallocatorを追加する — D1019の不採用を再実装し、原因を覆う過剰機構になる。
