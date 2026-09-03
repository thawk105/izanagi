---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-t2076-sort-oracle-ir-design
seq: 1
title: [T-2076] 依頼された設計は既に [T-2145] として着地済みで、残件は台帳 2 件と現役 docs 2 箇所だった (docs のみ、branch worktree-dev-wave-t2076-sort-oracle-ir-design、実装面の差分 0)
---

## 本文

ユーザーは「[T-2076] の設計 wave を起票し、設計文書へ『これは先行実験と別の実験である』ことを
明示的に書け」と依頼した。**着手前の一次資料照合で、その設計と実装が 2026-09-02 に [T-2145] と
して既に local main へ着地していることが分かった** (commit `23565ae55`、worklog entry 1214)。
新しい設計文書は作らず、依頼の充足を現物で確認したうえで、同じ着地が終端させた台帳の取りこぼしと、
その着地が自ら must-fix と裁定しながら落とした現役 docs を閉じた。一次資料と逐語は
`output/insights/2026-09-03_t2076-already-landed-closure/`。

- **依頼の 3 要件はいずれも landed main で満たされていた。** 「別実験である」の明示は
  `output/insights/2026-09-02_t2145-sort-oracle-ir/README.md:6-8`、
  `.claude/agents/coder-v4-autonomous-sort.md:93`、`orchestrator/campaign/p3_s4_loop_sort.py:317`。
  「D344 を supersede しない」は同 README:64 と agent file:94、同 loop:321。
  本 wave も D344 の実験同一性の論点に触れていない。
- **段 3 レンズ A が親 brief の中心主張を崩した。** 親は「残件は stale carry だけ」と書いたが、
  [T-2145] の段 6 裁定 F4 は `docs/phase3-s5-sort-runbook.md:190` を「親が段 7 で書く」と分割して
  おり、それが着地していなかった。**fix 子担当の 2 docstring は正しく着地しており、落ちたのは
  親担当の docs だけ**である。現役 runbook が新しい IR 実験を旧 raw C++ 実験の proof chain で
  説明したままになっていた。親が是正し、同型の `docs/phase3.md` 残課題 (c) も範囲に足した。
- **段 3 レンズ B が 2 件目の stale carry を見つけた。** `[T-1700]` も同じ着地で終端していた。
  文面が「非保証の明示を**維持**する」なので、放置は landed main が既に閉じた非保証を復活させる
  向きに働く。`[T-2076]` と同じ fragment で閉じた。
- **レンズ A は親自身の資料の欠陥も指摘した。** 親が子へ渡した D1355 の「逐語」コピーが末尾の
  却下選択肢 1 件を欠いていた。行範囲で切り出したのが原因で、指摘後に全文へ取り直した。
- **refuted は無い。** 両レンズとも「新しい独立した設計文書をもう一本作る必要はない」で一致した。
- **エージェント工数:** 段 3 の read-only consult 2 本 (並列、`lane=sol` / `lane=luna`) のみ。
  実装面の差分がゼロなので段 5・6 と変異 matrix は `DW-S04` により省いた。
- **[T-2145] の実装の正しさは再検証していない。** 本 wave が見たのは記録と landed コードの記述の
  一致だけである。「766 passed」「変異 11/11 KILLED」も独立には認定していない。
- **持ち越しの取りこぼし型:** 完了で閉じた wave の**親担当** must-fix が、fix 子担当分だけ着地して
  黙って落ちた。段 8 の routing 裁定は本エントリと同じ wave で行った。

## 次の一手差分

### 完了

- [T-2076] 設計と実装は [T-2145] (commit `23565ae55`、entry 1214) として着地済みで、
  「別実験である」の明示と「D344 を supersede しない」も landed main の逐語で満たされている。
  順序依存の後続 [T-2145] も着地済み。本 wave は充足を現物で照合し、落ちていた現役 docs
  2 箇所を是正した。
  remaining: none
  base: 38ba6031237b016617cf9bb0f33c2a575a467c010a286bd9ba306c94a3e473ab
- [T-1700] 「別の変更単位として比較裁定へ回す」は D1355 が果たし、その実装が [T-2145] として
  着地した。非保証の明示は landed main で admitted IR と versioned corpus に限った保証へ
  置き換わっており、維持すべき現行状態ではなくなっている。
  remaining: none
  base: eeb1ffd2fbafd98b7f69f79e29d067dcdcf0dabf30c2ecbd61a2fa2801f6e0b8
