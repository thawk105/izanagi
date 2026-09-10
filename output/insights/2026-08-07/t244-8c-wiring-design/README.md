# [T-244] 8c 結線の前提設計 wave — 逐語凍結と裁定

```
authority: none
default_effect: no-state-change
```

可変状態の正本ではない。設計の正本は `docs/phase3-8c-wiring-design.md`、
状態の正本は worklog 末尾と現行 phase doc である。

## 中身

| file | 何か |
|---|---|
| `brief.md` | 段 1 親 brief (scope・確定裁定・不変条件・実測前提・provisional 裁定 (P1)〜(P6)) |
| `parent-measured.md` | 段 1 の前提実測 (probe の逐語と出力。probe 自体は repo 外に置き、実行可能資材を repo へ持ち込まない) |
| `s2-plan.md` | 段 2 codex 設計プラン (read-only / effort max) |
| `s3-lensA.md` | 段 3 敵対レンズ A (恒真化・正しさ境界) — blocker 4 / must-fix 5、判定 NO-GO |
| `s3-lensB.md` | 段 3 敵対レンズ B (受理集合・順序・既定経路・§7 要件) — blocker 4 / must-fix 3、判定 NO-GO |
| `s4-adjudication.md` | 段 4 親裁定 (real / refuted、採否、裁定パッケージ 5 件) |

## この wave が名乗ってよいこと

> **[T-244] P3 の 8c 結線について、前提 5 点の exact contract を設計文書として起草し、
> 敵対 2 レンズの blocker 8 件を親が現物で裏取りして設計へ織り込み、
> 発行 3 条件は依然 0/3 だと確定した。**

名乗ってはならない — 結線の実装 / 発行 3 条件の充足 / P3・P4 の充足 /
production provisioning の解禁 / 物理実行の保証 / D114・D183・D201・D211 の緩和。

## 段 1 実測値 (現 HEAD `c9990bc2` の worktree)

- 批准値は現 parser を通る。`F=33`、codec feasibility = origin 75,206 / head-tx 30,753 bytes。
- 本番 authority は 71 bytes・`origins: []`、sha256
  `76fb551fa6aa637487211039fca5c365275c5f49cb926d59bba3511da152ffd2`。**本 wave で変更していない。**
- outcome 受理表 8 例、`batch_member_row_count_min` の `minimum=2`、`derive_cell_key` の 4 要素、
  event 6 種と phase 遷移、`_same_committed_request` の冪等条件を実測。

**実装差分が無いため、変異 matrix と受入全走は対象外である** (`DW-S04`)。変異事前登録も行っていない
(登録すべき変異面が存在しない)。将来の実装 wave 向けの変異登録候補は
`docs/phase3-8c-wiring-design.md` §12-7 に置いた。
