## 総括

**real／must-fix 1件。実機動作は未確認で、green・closedではありません。**

- **real：manual probeの改行が二重エスケープされています。**
  [test_t2397_a1_source.py:31](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/manual_probes/test_t2397_a1_source.py:31)、35・36・69行。ASTで文字列値が改行ではなく文字列 `\n` であることを確認しました。31行の切断が成立せず、36行のシェル前置きも正しく構文解析できません。69行もJSONLの行区切りになりません。
  **成果物影響：承認済み正例が依存staging前に停止し、全6 armの実機証拠を作れません。**
  最小fix：4箇所の `\\n` をPythonの改行エスケープ `\n` に修正。
  closed条件：抽出シェルの構文・終端確認、computeで全3 workload／6 armの関門・trace/perf build・verify完走、JSONLの各行decode、M1・M2の期待赤。

- **refuted（静的確認）：** prefix／FetchContent 5値の転送脱落、exact argv consumerの4 define取り残し、CMake警告無視、tracked-clean偽装、T2514の最初のredでの打切りは確認されませんでした。既存負例の反転・skipもありません。

- **未確認：** submit→qsub→job→terminal→complete/materializeの実機完走、関連pytest・変異検査。今回は実行していません。

追加の読取り検査はPreToolUse hookに拒否されました。シェルファイルを読むPythonコマンドがdispatch必須処理と判定されたためで、その検査結果は未取得です。
