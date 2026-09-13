# 段 4 裁定 (親) — [T-2547]

段 2 plan と段 3 敵対 2 本の所見を real / refuted、採用 / 不採用、scope 内 / 外へ裁定した。

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| R1 | plan・sol・luna | 親の pin 閉包の断言 3 つ (「唯一」「`### 5.1` より後ろは一切読まない」「pin されていない」) が過大。`p3_b4_admission_record.py` は宣言 commit の**文書全体 sha256** と HEAD blob 一致を要求する | **real・採用 (scope 内)**。親が追加実測: admission record は 3 driver 分いずれも不在 (`git ls-files docs/` grep 空、rc=1)。無効化される既存 admission は 0 件。追補では admission に触れない (scope 外)。**訂正の反映は段 6 後に行った** — `census-and-pin-closure.md` 冒頭へ撤回を明記し、正した版を `output/insights/2026-09-14_t2547-b4-descriptive-erratum/census-verbatim.md` に置いた (段 6 の両レンズが「訂正済みと書いたが提供物に残っている」を `partial` として正しく指摘した) |
| R2 | plan・sol・luna | 発火根拠は §5.1.1 の「適格な block を 201 件確保できない場合」であり、§5.1 の「予算上」ではない | **real・採用**。追補本文へ明記した |
| R3 | sol・luna | 親の mtime 推論は根拠不足。luna は worktree では mtime が再現しないと実測 | **real・採用**。追補には最初から mtime 論拠を入れていない。段 6 後に `census-verbatim.md` の「撤回した論拠」節へ撤回を明記し、`census-and-pin-closure.md` 冒頭にも同じ撤回を書いた。**「今回 0 件」は再読取りが支持するが「前回以降増えていない」は証明されていない**と分けて述べる |
| R4 | sol | 適格性条件 3〜6 (校正済み workload 所属 / 固定 bootstrap 集合 / 共通 reference の一意性 / 両アーム digest 非汚染) は §5 の該当欄が未記入なので適格性を確認できない。3 loop の lock は `reflux:on` | **real・採用 (insight へ記録)**。結論 0 件を強める方向。適格条件そのものは変えない |
| R5 | luna | **must-fix**: 追補は機械出力を 1 つも変えない。brief の成果説明が「材料レポートの報告型が機械的に変わる」と誤読される | **real・採用**。追補へ「限定するのは人が報告に書いてよい主張の上限だけ」「機械が生成する材料レポートの値・分類・参照は 1 つも変わらない」を明記した |
| R6 | luna | 「合成ループから得た適格な少数の赤 precursor を使う」は適格 0 件のため現在実行できない。その未達を書くべき | **real・採用**。追補へ「方針は維持するが、その利用は本追記では実現していない」を明記した |
| R7 | luna | 文言 6 件が曖昧 (「実走前」「宣言」「記述統計」「有意性」「B-4 は」「今回の根拠」) | **real・採用**。全件直した。「記述統計」の指示対象、「有意性を主張しない」が拘束であって観測結果でないこと、「本書に基づく B-4」への限定、調査範囲の限定、supersede 未裁定の維持をすべて明記 |
| R8 | luna | 焦点走に `orchestrator/tests/test_real_repo_serialization.py` が漏れている (3 driver test module を import する) | **real・採用**。14 file へ拡張して実走した |
| R9 | luna | plan が §10 を不適切と切り捨てる理由が強すぎる | **real だが成果物への作用なし**。置き場所は §5.1 のまま (plan・sol・luna の 3 者とも §5.1 を妥当と判定)。記録のみ |
| R10 | luna | D1936 の「少数赤利用」方針と `design_not_feasible` / D1880 の 201 行契約の関係が未解消 | **real・scope 外**。裁定パッケージとしてユーザーへ返す。新機構・受理緩和は作らない (依頼の明示境界) |
| R11 | luna | living doc checker は意味的な再掲を検出しない。追補が挙げる campaign file path は可変参照 | **real・採用**。逐語の耐久記録を insight 側に置き、追補は日付付きの過去観測として書いた |

**refuted / 不採用はゼロ。** 両レンズの所見はすべて real と裁定した。

## 変異 matrix

実装面 (D95 決定 2) の差分がゼロ (`docs/**.md` のみ) のため `DW-S04` により免除する。
受入全走は免除しない。

## 親が実走した検査 (段 4〜5 時点)

- `git diff --stat`: 1 file / 37 insertions / 0 deletions。`git diff --check` rc=0。
- `python3 tools/check_docs.py` rc=0 (`check_docs: 違反なし`)。編集前の baseline も rc=0。
- 焦点走 14 file: `1085 passed, 1 skipped`、rc=0。Pegasus 計算ノードへ dispatch
  (request `996048.nqsv`、Elapse 150S、child rc=0)。**凍結 §5.1.1 の raw / semantic sha256 pin は無傷。**
