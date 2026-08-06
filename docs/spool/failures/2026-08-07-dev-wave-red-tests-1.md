---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-07
wave: dev-wave-red-tests
seq: 1
---

## 新規

### {{F:acceptance-shape-silent-gate-skip}}. 受入全走に `-rf` を足したら事前検査 2 件が黙って発火しなくなった [恒真ゲート] [手順漏れ]

- 事象: 親が `python3 tools/run_tests.py -rf` を「受入全走」として走らせ、
  6837 passed / 20 skipped を台帳へ書こうとした。実際にはこの形は `_is_acceptance_run()` が
  False を返す形であり、**未 stage 削除検査と RuleOps 台帳検査の 2 つの事前検査が発火していない**。
  テスト node は同じ数だけ走り、警告も出ないため出力からは区別できない。
  段 3 の敵対検証子が file:line で指摘して露見した。
- 実測: `tools/run_tests.py` を直接 import して分類器を呼ぶと
  `[]` → acceptance=True、`['-rf']` → acceptance=False、`['-q']` → acceptance=True、
  `['orchestrator/tests']` → acceptance=True / full=False。
  許される compact option は `q` と `v` だけである。
- 根本原因: report flag は「出力を増やすだけの無害な追加」に見えるが、受入形の判定は
  引数列全体の形で決まる。**gate を失っても静かに成功する**ため、気づく手がかりが出力に無い。
- 同時刻に **別 wave も `run_tests.py -rf` を受入として走らせていた** (独立 2 例)。
  単発の不注意ではなく、この形が自然に選ばれることを示す。
- 恒久対応: memory `acceptance-run-takes-no-extra-flags` (受入として記録する走行は引数なし、
  逐語や skip ラベルが要るなら受入形とは別の走行を立てる)。
  **`run_tests.py` が受入形でない走行に 1 行警告を出す改修**は
  `output/insights/2026-08-07_red-test-audit/README.md` の裁定パッケージでユーザーへ諮っている。
- 再発検知: 上記分類器を引数列に対して直接呼べば真偽が出る。
  受入結果を台帳へ書く前に、走らせた引数列そのものを記録に残す。
- 近縁: F37 (検査 rc をパイプで握り潰す — 「検査が実は走っていないのに緑と読む」同じ根)。
