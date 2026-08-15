# 2026-08-16 freeze 由来 holdout の実測境界に admission と一回性台帳を置く — 材料

dev-wave (branch `worktree-dev-wave-t523-holdout-admission`) の一次資料。
可変状態の正本は worklog 末尾エントリであり、本ディレクトリは逐語と実測値を保持する。

## 構成

| path | 内容 |
|---|---|
| `brief.md` | 段 1 brief (親の実測と provisional 裁定 P1-P5) |
| `s4-adjudication.md` | 段 4 裁定 + プラン v2 (採用 13 / scope 外 5 / 変異事前登録) |
| `s6-adjudication.md` | 焦点再レビュー後の親裁定 (残 5 所見の real/refuted と保証の縮小) |
| `verbatim/s2-plan-v1.md` | 段 2 プラン起草 (親 brief の誤り 6 点を含む) |
| `verbatim/s3-consult-a-sol.md` | 段 3 敵対相談 レンズ A (NO-GO) |
| `verbatim/s3-consult-b-luna.md` | 段 3 敵対相談 レンズ B (NO-GO) |
| `verbatim/s5-author-unit1.md` | 段 5 実装 Unit 1 報告 |
| `verbatim/s5-author-unit2.md` | 段 5 実装 Unit 2 報告 |
| `verbatim/s6-review-a.md` | 段 6 敵対レビュー レンズ A (NO-GO) |
| `verbatim/s6-review-b.md` | 段 6 敵対レビュー レンズ B (NO-GO) |
| `verbatim/s6-fix-unit-{a,b,c,d,e}.md` | 段 6 fix 各巡の報告 |
| `verbatim/s6-focus-rereview.md` | 段 6 焦点再レビュー (16 件の対応表と新規 5 所見) |
| `mutation/mutation-spec.json` | 本走の変異 spec (期待 node は完全集合) |
| `mutation/mutation-result.json` | 本走の変異台帳 (8/8 KILLED) |
| `mutation/mutation-spec-round1-probe.json` | 第 1 走 (probe) の spec |
| `mutation/mutation-result-round1-probe.json` | 第 1 走 (probe) の台帳 — erratum として保持 |

## 変異台帳の trim について

`mutation-result*.json` は原本が 5.7-5.9 MB あり、その大半は各 mutant の runner stdout 全文である。
**巨大な stdout 全文だけを sha256 + byte 数へ置換して保存した。**
`status` / `rc` / `failed_nodes` / 各種 hash は無改変であり、原本の sha256 と byte 数は
各ファイルの `_trimmed_from_original` に記録してある。

## 変異結果 (本走)

固定 HEAD `63a2473b2966824a6141ef202998ff46b485e695`、runner-mode=dispatch、
8 変異 + baseline の 9 走。**KILLED 8 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0。**

| id | 変異 | 検出 node 数 |
|---|---|---|
| M1 | 保護 signature の導出を空集合にする | 101 |
| M2 | 実行 gateway の許可検査を削除する | 24 |
| M3 | `--flagfile` を間接入力の拒否対象から外す | 4 |
| M4 | cell 確保の `O_EXCL` を外す | 4 |
| M5 | attempt ticket の二重消費を許す | 2 |
| M6 | freeze 由来集合と中立表の exact 一致検査を削除する | 1 |
| M7 | 許可証の同一性検査を型検査へ緩める | 5 |
| P1 | 正例 — 許可証なしの実測をすべて拒否する (過剰拒否) | 5 |

第 1 走 (probe) は期待 node の完全集合を確定するために行い、8 件とも rc=1 で
検出側へ倒れたが node 集合が MISMATCH だった。実測集合で再登録して本走を行った。
本走の runner からは、実行時にサフィックスが付く real-repo 変種 1 件を `--deselect` した
(collection 時 ID と実行時 ID が異なり事前登録できないため)。**当該 test は受入全走で担保される。**
