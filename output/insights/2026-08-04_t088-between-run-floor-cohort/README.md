# 2026-08-04 — between-run floor は 1 submission cohort で確立しない (逐語)

dev-wave (branch `worktree-wave-t088-floor`) の子成果物の逐語凍結。
裁定と要約は worklog 本エントリと decisions 側が正本で、ここは加工前の一次資料だけを置く。

| ファイル | 出所 | 役割 |
|---|---|---|
| `00-parent-brief.md` | 親 (Claude) | 段 1 brief。前提実測 6 件と (P1)〜(P6) |
| `01-plan-codex.md` | codex `gpt-5.6-sol` / reasoning=max / read-only | 段 2 プラン (file:line 粒度) |
| `02-lens-a-statistics.md` | 同上 (別 context) | 段 3 敵対レンズ A = 統計的妥当性と測定の意味論 |
| `03-lens-b-integrity.md` | 同上 (別 context) | 段 3 敵対レンズ B = 実装整合・防壁・実効性 |

## この資料の読みどころ

- **2 レンズが独立に NO-GO を返した。** 攻撃面 (統計 / 実装) を分けたのに、
  結論と最重要所見が一致した (時間窓 cluster = 1 では floor にならない)。
- **親 brief の誤りが 4 件、子によって file:line で反証されている** (D 番号の誤引用、
  飽和判定の読み違い、pin 数の過少計上、task 同一性のすり替え)。
  `00-parent-brief.md` は訂正前の原文であり、**訂正は worklog 本エントリが持つ**。
  この逐語を単独で引くと誤りをそのまま継承するので注意する。
- レンズ B の B3 (計算ノードの `python3` = 3.9) と B4 (`--job-script` の無条件受理) は、
  親が独立に file:line で裏取りして real と裁定した。

## 実測しなかったこと

PBS job は 1 本も投入していない。子はいずれも read-only sandbox で、pytest を実走していない。
数値の主張はすべて既存 artifact の field と静的検査に基づく。
