## 対応表

| 項目 | 状態 | 実装箇所 |
|---|---|---|
| F-M1 | closed | [生成器:99](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:99) で read 比以外の11条件を比較し、[load_data:218](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/tools/plotting/plot_p2_5_search_cost.py:218) で出力前に検査。caption も共通値を使用。 |
| F-S1 | closed | [test:62](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig1-unit-a/orchestrator/tests/test_plot_p2_5_search_cost.py:62) で実データ由来の1 campaign の threads を変え、`FigureDataError` を確認。 |

## 変更

- 生成器: **395/450 行**
- test: **217/300 行**

編集したのは上記2ファイルのみです。

## 変異の位置

M14 の置換アンカーは `if any(any(c[key] != common[key] for key in keys) for c in conditions[1:]):` → `if False:`。出現は **1回**で、`test_measurement_conditions_across_campaigns` が赤になるはずです。既存 M1〜M13・C0 のアンカーはすべて引き続き各1回です。

## 実走

`py_compile`、生成器の実走、自走 harness が成功しました。harness は **13 passed、0 failed、1 skipped、0 errors**。skip は親の着地 bundle を待つ `test_landed_bundle` です。変異そのもの、全体テスト、pytest は未実走です。`.scratch-fig1/` は削除済みです。

## 総括

裁定2の採用項目 F-M1・F-S1 を反映しました。