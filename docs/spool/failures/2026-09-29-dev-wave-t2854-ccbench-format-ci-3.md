---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-t2854-ccbench-format-ci
seq: 3
---

## 新規

### {{F:t2854-criterion-perturbed-by-own-change}}. 親が段 4 の完了条件を、足させる変更自身が出力に現れる観測量で書き、実装子が不成立を実測して停止した [手順漏れ] [テスト代表性]

- 事象: [T-2854] pin 前進 (1)(2) の段 4 裁定 R1 で、整形後に TRACE=0 の行番号を戻す `#line` を足させ、完了条件を「`-P` なしの前処理出力 (行番号マーカー込み) が C2' と byte 一致」と書いた。`#line` 自身が前処理出力に行番号マーカーを出すので、この条件は `#line` を足すかぎり原理的に成立しない。実装子 A は不成立を実測して規定どおり停止した (140 秒、9 call)。親が守るべき性質 (TRACE=0 で出力される各コード行の推定行番号の列) に直した追補を出し、続きの A2 で成立した。
- 根本原因: 親は「行番号がずれないこと」を確かめる手段として、手元にあった行番号マーカーの byte 比較をそのまま完了条件にした。依頼する変更 (`#line` の追加) がその観測量を必ず変えることを確かめなかった。
- 恒久対応: 完了条件を書く前に、依頼する変更自身がその観測量に現れないかを確かめ、守るべき性質そのもの (ここでは推定行番号の列、`__LINE__` の展開値) を観測量にする。性質の定義は参照実装つきで渡す (本 wave の `probe/presumed_lines.py`、insight `output/insights/2026-09-29/t2854-ccbench-format-ci/README.md` §5.2)。memory `completion-criterion-must-not-observe-own-change`。
- 再発検知: 実装子が「完了条件が成立しない」と実測して停止する (fail-closed)。

## 再発

### F819

- **再発: 2026-09-29** — [T-2854] pin 前進 (1)(2) の段 6 review の投げ文に、親が必読 path を相対 (`probe/line_macro_probe.log`) で書き足し、子が直前の `review/` からの相対と読んで存在しないため即停止した (rc=1、70 秒、6 call)。全 path を絶対化して再投入した。結末は fail-closed で、型 (親の投げ文の path が子の解決先と食い違う) は同じ。
