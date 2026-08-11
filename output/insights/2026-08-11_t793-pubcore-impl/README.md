# [T-793] 公表層の機械執行 — wave 成果物

- wave: `dev-wave-t793-pubcore-impl` / 2026-08-11
- branch: `worktree-dev-wave-t793-pubcore-impl`
- trust root `F_p` = `b13b7ea840ad51199f40b3a534c9d1cdb422af2e` (D291 の fold commit。起動時に実測で再同定)

## 結論

**4 必須要件のうち本 wave が閉じたのは (ii)・(iv)・(iv-b) と (i) の識別束縛だけである。**
**(iii) と (i) の原子性は承認済み文書・機械防壁との衝突により閉じられず、
`package.md` の R1〜R5 でユーザー再裁定へ返した。**

**本 wave は「公表層を機械執行した」と主張しない。**
公表 core v2 §10.4 の 11 変異のうち、実成果物経路で拒否できるのは **0/11**、
直接 parser の負例として拒否できるのは **#7 と #9 の 2/11** である。

## 実装したもの

新規 package `orchestrator/publication/` (`orchestrator/preregistration/` は 1 file も変更していない)。

| file | 要件 | 内容 |
|---|---|---|
| `approval_d291.py` | (iv) | D291 承認 payload の parser / resolver。trust root は `F_p` を module literal で固定 |
| `report.py` | (iv) | deny-only の構造化 report と決定的 JSON CLI。後続 supersession を fail-closed で走査 |
| `ledger.py` | (i) 識別束縛 | 固定 literal からの無引数 canonical path 導出。**予約 writer なし** |
| `approval_guard.py` | (ii) | 未確定 marker gate |
| `addendum_p_envelope.py` | (iv-b) | 追補 P の `p01`〜`p03` exact-key (production caller なし) |
| `tools/spool_fold.py` | (ii) | marker gate を fold 3 経路へ結線 |

`output/registry/t139-publication-reservations.jsonl` は **0 byte** で、予約 entry は 1 行も無い。

## 段ごとの結果

| 段 | 結果 |
|---|---|
| 段 2 プラン (sol / max) | **NO-GO**。(iii) の授権未確定、親の (P5) を否定 |
| 段 3 レンズ A (sol) / B (luna、ともに max) | ともに **NO-GO**。所見 11 / 9 件、blocker 8 / 3 |
| 段 5 実装 3 lane (sol / high) | lane A 33 passed 2 failed、lane B 20 passed、lane C 自前緑 |
| 段 6 レビュー C / D (sol / high) | ともに **NO-GO**。blocker 5 件 |
| 段 6 fix 2 本 (sol / high) | 全 blocker を closed |
| 段 6 fix 後の実走 | **204 passed / 4 failed** (4 件は焦点走の import path 偽赤で非帰属) |
| 変異 matrix | `mutation/mutation-ledger.json` |
| 受入全走 | `package.md` と worklog に記録 |

## 逐語

`verbatim/` に段 1〜6 の子出力を凍結する。
