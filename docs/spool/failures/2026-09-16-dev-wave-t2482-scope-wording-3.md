---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2482-scope-wording
seq: 3
---

## 再発

### F28

- **再発: 2026-09-16 (near miss)** — 段 4 で登録した変異の anchor (old 逐語) が、段 6 fix 後の source では
  文字列 literal の行分割によって行境界を跨ぎ、`DW-M07` の再検証 (`--plan-only`) が anchor count=0 で
  止まった。親は anchor を 1 行に閉じた形へ再照準したが、その際に削除範囲が登録 (先頭空白 + 括弧句) と
  異なる形 (括弧句 + 読点) になり、probe / final の両走がその変異で走った。赤の理由と node 集合は登録と
  同じで KILLED したが、登録どおりの単独変異の実測ではなかった。段 6 の焦点再レビューが台帳と裁定の
  差を検出し、行境界を跨ぐ複数行 anchor で登録どおりの変異を補走 (KILLED、期待 node 完全一致) して、
  元の走行を erratum として残した。**恒久対応の追補 = anchor count=0 での再照準は削除内容を変えず、
  行分割は old / new に改行を含めた複数行 anchor で吸収する。再照準した変異は裁定へ追補として書き、
  段 6 の焦点再レビューに「台帳の replacements と登録の逐語一致」を点検項目として渡す。**
  一次資料は `output/insights/2026-09-16/t2482-scope-wording/README.md` の変異台帳節。
