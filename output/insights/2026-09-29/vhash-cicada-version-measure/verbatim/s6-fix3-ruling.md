# 段 6 fix 3 巡目の裁定 — 計算ノード smoke で露見した実機 blocker (2026-09-29 06:4x JST)

入力: smoke1 (request 33792.nqsv、checkout = wave worktree @44c37d6d8、Elapse 41 s、child rc=1)。
dispatch log: /work/1/SFC/tanab/tmp/vhash-cicada-version-measure-2026-09-29/dispatch/smoke1.log。
事実: 依存物準備と stock build は完了し、`_delay_compile` の `RuntimeError: Cicada transaction compile command not unique` で停止。raw JSON は書かれなかった (例外が main から抜けた)。
原因: external/ccbench/cmake/ProtocolHelpers.cmake:32-34 が workload ごと (ycsb/tpcc/bomb/sbomb) に `add_executable(${wl}_${name} ... ${P_SOURCES})` するので、`compile_commands.json` に `cc/cicada/transaction.cc` の行が 4 つある。
DW-O16 の「親の実機 blocker は別枠」として fix する (焦点再レビューの巡数には数えない)。

| # | 内容 | fix |
|---|---|---|
| H1 | `_delay_compile` の行選択 | `ycsb_cicada.exe` target の行 (出力 path `output` field または `-o` の値に `ycsb_cicada` を含む行) を一意に選ぶ。0 件・複数件は従来どおり拒否 |
| H2 | smoke が途中の 1 段の失敗で全体を失う | smoke の各段 (stock build、delay compile、既定 build、有効 build、witness、較正、短い走) を個別に実行し、失敗段は `{"error": "<型>: <文>", "stderr_tail": ...}` を記録して、依存しない後続段は続ける (例: delay compile の失敗は後続を止めない。有効 build の失敗は短い走だけを飛ばす)。smoke の合格判定 (終了 rc) は従来どおり全段成功を要求し、緩めない |
| H3 | 例外で raw JSON が残らない | `main` は smoke / measure の例外を捕まえて `error` field 付きの JSON を必ず書き、rc=1 で終える (前例 silo_policy_coverage.py:769-777 と同じ形)。`_smoke_records` (measure の入口検査) は error 付き smoke JSON を拒否し続けること |

test: H1 は複数 target 行を持つ `compile_commands.json` fixture で ycsb 行だけが選ばれること・ycsb 行が 0/2 件なら拒否を検査。H2/H3 は「delay compile が失敗しても JSON が書かれ、他段の結果が残り、rc=1」「error 付き smoke JSON を measure が拒否」を検査。
変異の事前登録の追加:
- MUT-9 (H1): 行選択の ycsb 条件を外す (全 transaction.cc 行から先頭を採る) → 複数 target fixture の test が KILLED
