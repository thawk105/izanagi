---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1548-sigterm-sync-point
seq: 2
---

## {{D:empty-flaky-registry-attestation}}. 隔離台帳が空でも走行末尾の要約行を必ず出す

**決定:** flaky-node 隔離の要約行 `IZANAGI_FLAKY_HOLD_SUMMARY_V1` は、registry が空のときも
controller が必ず 1 行出す。値は `registered_node_count` / `matched_node_count` /
`skipped_node_count` がすべて 0 と、空 registry の digest である。
非空時の出力条件・形式・値は変えない。

**理由:**

- D697 決定 4 は「隔離は走行末尾の要約に必ず出す」と定めるが、実装は matched が非空のときだけ
  行を書いていた。隔離対象が 0 件になった瞬間に行自体が消える。
- その状態では、**「隔離ゼロ」と「隔離 hook が load / 配送 / 集約されていない」が同じ出力になる。**
  隔離は本質的に検査を走らせなくする操作であり、機構が生きていることの走行時 attestation を
  失うと、絶対規律 2 が要求する「正しさゲートを緩める変更を検出できる状態」が保てない。
- 隔離件数が 0 の状態は運用目標であって例外ではない。目標状態でだけ attestation が消えるのは、
  最も長く続く状態で最も証拠が薄いということである。
- 空を含めて常に出すことで、受入走行の出力から registry の digest が常に読める。
  将来 entry を足したときの差分も同じ行で追える。

**却下した選択肢:**

- 空のときは行を出さないまま、別の行で hook の生存を示す — 出所が 2 つに割れ、
  どちらが欠けたのかを受領証から判定できない。
- 空のときだけ別 schema の行を出す — consumer が 2 形式を扱うことになり、
  digest の比較が形式境界をまたぐ。
- 空 registry を禁止し続け、隔離解除時にダミー entry を残す — D697 決定 2 の受理 6 条件を
  満たさない entry を台帳へ置くことになり、証拠束縛の意味が壊れる。
