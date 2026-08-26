# 2026-08-26 [T-1759] [T-1742] 批准台帳の履歴検査を DAG として読み直す

wave: `dev-wave-t1759-t1742-ratification-history`
branch: `worktree-dev-wave-t1759-t1742-ratification-history`
着手時の local main: `9463bcbcb1541625db59abb97cf6a76934b4c80c`

## この wave が変えたこと

`orchestrator/campaign/enforcement_source_ratification.py` の
`_committed_ratification_digests()` を、`git log --full-history <台帳 path>` が返す版を
線形に並べて byte 前置拡張を求める形から、HEAD の到達可能 DAG を自前で列挙して
遷移として検査する形へ置き換えた。台帳 bytes、closure digest の定義、批准の人間手番、
`require_ratified_closure()` の署名と `enforcement-source-closure-unratified` の文言は変えていない。

規則の正本は D994、環境前提の正本は D995 とする。

## 実測 (この checkout で親が測った値)

| 測ったもの | 修理前 | 修理後 |
|---|---|---|
| 実 main での検査 | `ratification history is not a strict prefix extension` で赤 | 受理集合 1 件を読む |
| `require_ratified_closure()` の終端 | 上記の赤 | `enforcement-source-closure-unratified` |
| 所要 | — | 0.436 秒 |
| git 呼出し | 19 回 (版 17 + 2) | 9 回 (= 6 + D 2 + B 1) |

- 台帳 blob は開設 commit 以来 byte 不変で 1 行。`--full-history` が数える版は 17、
  うち 16 が merge で、すべて「片方の親が台帳を持たない」ために列挙されていた。
- 呼出し回数の式は `6 + D + B`。D は台帳を持つ commit に現れる異なる `hooks` tree 数、
  B は異なる台帳 blob 数 (= 批准回数)。**D の上界は全史 6469 commit にわたって 44** であり、
  1 process あたり 10 秒の timeout とは桁が違う。
- この module 自身が enforcement closure の 25 path の 1 つなので、この修理で closure digest は
  動いた。修理後の現行値は `dabeada30868a5f790b25b86a9f0a34fafb24946f0e73de48fb90d97d9332eb9`、
  台帳の唯一の行は `db511c3d841128bfdbf5ba7c6bbdb2ce4da1fe0fdefe8d52aaacb0906ddeea44`。

## 規則を実装前に検証した合成履歴

親が repo 外の使い捨て probe で、確定した規則を 9 つの合成履歴と実 main へ当てた。

| 履歴 | 期待 | 結果 |
|---|---|---|
| 分岐 2 branch がそれぞれ 1 行追記して合流 | 受理 (3 行) | 一致 |
| 台帳より前に分岐した branch の merge | 受理 (1 行) | 一致 |
| cherry-pick による中間挿入 | 受理 (3 行) | 一致 |
| 逆順に追記した 2 枝の合流 | 受理 (3 行) | 一致 |
| octopus (3 親) | 受理 (4 行) | 一致 |
| 独立した台帳導入 2 件 + 合流 | 拒否 | 一致 |
| 履歴中間での行の置換 | 拒否 | 一致 |
| 合流が片方の親の行を落とす | 拒否 | 一致 |
| 合流が 2 行足す | 拒否 | 一致 |
| 実 main 履歴 | 受理 (1 行) | 一致 |

## 変異 matrix

`mutation-spec-final.json` と `mutation-result-digest.json` が台帳。
baseline PASSED、**10/10 KILLED**、SURVIVED 0、MISMATCH 0、期待 node 集合は全件一致。

初回 probe では過剰拒否の正例 `MUT-T1742-MERGE-ORDER` が SURVIVED だった。原因は変異が
弱かったことで、`len(parents) == 1` を `>= 1` にする形では合流でも「最初の台帳親」しか
順序を見ず、逆順追記の合流テストが偶然通る。実効 gate は「全ての台帳親の順序を保存させる」
形なので、条件全体を `any(not _is_subsequence(rows_at(parent), rows) for parent in
bearing_parents)` へ差し替えて再照準した (DW-M02)。再照準版の node 集合は DW-O19 の
一時変異で直接測り、`test_opposite_branch_orders_are_accepted_after_merge` の 1 件ちょうどだった。

走行は 3 回行った。1 回目と 2 回目は wrapper の共有木事後検査 (`rc=125`) で無効化され、
3 回目に対象 commit だけを持つ独立 clone を `--source-repo` へ渡して完走した (F300 の再発)。

## 実装しないと裁定した real 所見

- gate の射程が新規 lock 作成経路に限られ、artifact 受入と dispatch に届いていない。
- 撤回 (revocation) の意味づけが未裁定。既定は「批准は永久」。
- shallow と graft の存在確認は check-then-use であり、検査中の書き換えには対応しない。
- 合流が示すのは「親に行があったこと」だけで、各追記が人間批准であることは示さない。
  これは D526 が既に定めた線であり、認証は D905 の執行主体が担う。

## 逐語

`verbatim/` に段 2 plan、段 3 敵対相談 2 本、段 5 実装、段 6 レビュー 2 本、fix、
焦点再レビューの子出力を置く。すべて `tools/check_codex_output.py` rc=0 で採用したもの。

**erratum (可逆最小正規化)。** `verbatim/s6-review-luna.md` は原文の 101 / 104 / 107 / 110 / 113
行目が末尾に半角空白 2 個 (markdown の改行) を持ち、`git diff --check` に抵触した。
DW-S07 の規定に従い、可視文字を変えずに各行の末尾空白だけを落とした。

- 原文 sha256: `f2aab1c64298de9c3dec788ffe978dca2dadf3c1ad7f1ec823d35214ea50f0cc` / 9411 bytes
- 収録 sha256: `f68f82703299a196b7e41bb38d86085761718091f1383857074ea5fc35e85c24` / 9401 bytes
- 復元法: 上記 5 行の行末へ半角空白 2 個を戻すと原文 bytes に一致する (差は 10 bytes)。
