---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t1396-c04-reject-started
seq: 1
---

## {{D:c04-no-redundant-registry-check}}. 到達検査から含意される存在検査を判定器へ足さない

**決定:** s8c の判定器へ到達対象 (`_declared_call` の target) を足すとき、**同じ symbol に
対する `_functions(<module>)` の存在検査を併せて足さない**。既存の C04 が
`forbid_trial_restart` について両方を持っているのは先行実装の名残であり、対称性を理由に
新しい対象へ複製しない。

**理由:**

- resolver は対象名が target module の関数集合にあるときだけ target を `graph.calls` へ入れ、
  `_declared_call` はその membership を要求する。したがって `_declared_call` が真なら
  後段の存在検査は必ず真になる。定義が欠ければ先行層が `crash-policy-cell-partial` で
  先に return するので、後段の `restart-guard-absent` へ到達する入力は作れない。
- 冗長な層は同じ入力を二重に拒否するため、変異の単一理由性 (`DW-M01`) を壊す。赤理由が
  一つに絞れない変異は事前登録できず、実効 gate の証拠にならない。
- 段 3 の敵対相談 2 本が、異なるレンズから独立に同じ結論へ到達した。片方は正しさ境界の
  レンズ、もう片方は変異帰属のレンズである。

**却下した選択肢:**

- 対称性のために足す — 受理集合も report の reason も変えず、観測できる効果がない。
- 後段の reason code を新設して到達させる — 到達不能な分岐へ名前を付けるだけで、
  恒真な関門を 1 つ増やす。
