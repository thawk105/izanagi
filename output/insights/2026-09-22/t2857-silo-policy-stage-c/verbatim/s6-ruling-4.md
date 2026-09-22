# 段 6 裁定 4 巡目 — [T-2857] (2026-09-22 21:4x JST、親 = Claude manager)

入力: 焦点走 f5 (18161.nqsv、100 passed / 0 failed / 2 skipped)、coverage-2 (18167.nqsv、Elapse 40 秒、結果 = job dir `coverage-2.json`、
error = `RuntimeError: owner TU compile command is not unique`)。fix-3 の H1 は効いた: 準備用 stock build の後、最初の case の gate は通り build まで進んだ。

| # | 出所 | 内容 | 判定 | 扱い |
|---|---|---|---|---|
| I1 | coverage-2 | silo は `ccbench_add_protocol(silo ... WORKLOADS ycsb tpcc bomb sbomb)` (`external/ccbench/cc/silo/CMakeLists.txt:1-3`) で `transaction.cc` が 4 実行体へ compile され、`compile_commands.json` にその行が 4 本ある。driver の `_owner_command` は 1 本を前提にして止まる | real | fix。condition gate と同じく、行の `output` が `CMakeFiles/ycsb_silo.exe.dir/` を含むものに絞る (`condition_meaning_gate.py:1902-1905` の選び方に揃える) |
| I2 | 1 投入 1 欠陥の型 (記憶: 起動時検査は 1 投入で 1 件しか欠陥を出さない) | 実走のたびに次の実行時の欠陥が 1 つずつ見つかる | 手順の是正 | fix-4 で、coverage と smoke の全 case の実行経路の前提を実機の構造 (既存 driver・CCBench の CMake・実行体の CLI・verifier の入出力) と照合し、見つかった不一致をまとめて直す |
