# [T-1068] 段 6 所見の裁定 (fix 1 巡目の前)

入力: out/s6-review-A.md (受理、NO-GO)、out/s6-review-B.md (受理、GO)、焦点走 focus-1 (計算ノード 31344.nqsv、commit 56b810852、10 failed / 5159 passed / 26 skipped、441 s)。

| 所見 | 判定 | 採否 | 処置 |
|---|---|---|---|
| A-1 test_buildcache_v2 の fixture 置換が `void TxExecutor::abort() {` を探して ValueError | real (焦点走で 7 件再現: `test_qualification_stock_build_case_dependency_options[*]`) | 採用 (must-fix) | fix-1 F1: fixture の形を canonical へ。期待値は変えない |
| 焦点走の reflux 3 件 (A・B とも静的に未検出) | real。`source_digest` が合成 checkout の `#if ADD_ANALYSIS` を未知マクロとして fail-closed (T-148)。実 CCBench は Options.cmake で ADD_ANALYSIS を universal 定義 | 採用 (must-fix) | fix-1 F2: 合成 Options.cmake に実物と同じ形で ADD_ANALYSIS を供給。source_digest / CONTEXT_MACROS は変えない (規律 2) |
| A-2 宣言行より前の前処理・行継続・BOM・`#line` は受理しうる | real、別経路 | scope 外 | docstring の限定どおり。R4/R5/R7 閉鎖の証拠に含めない。insight に残る限界として書く |
| B-1 import 時の宣言行検査は plan 外 | refuted | 不採用 | `HEAD[len(宣言行):]` の切り出しが宣言行で始まることを前提にするための assert で、既存 hole の RuntimeError と同型。author prompt で親が指示した |
| B-2 tally 正例の require 呼出しが重複 | nit | 不採用 | 受理集合に影響なし。derive だけで M3 は殺される (変異 probe で確認) |

変異の追加登録: なし (A-1・F2 は fixture の形の欠陥で、新しい受理・拒否の分岐を生まない)。M4 = `endswith(tuple(b"\n" + p for p in ...))`、M5 = 宣言行直後〜`  // remove inserted records` 前を任意 bytes とする照合、で具体化する (A 総括の提案を採用)。
