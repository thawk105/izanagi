# [T-2871] 段 6 裁定 2 (親) — 焦点走 3 回目 (33653.nqsv、d95c893ce、Elapse 44 s) の赤 4 件

焦点走: 4 failed, 389 passed in 38.43s (focus3.log)。skip は 0 件 (T1〜T3 は skip されず実行された、R6 の実測)。

| # | 赤 | 原因 (失敗本文から) | 裁定 | 処置 |
|---|---|---|---|---|
| R9 | `test_pair_pegasus_two_processes_use_distinct_claims_and_measurement_wal`・`test_pair_pegasus_crash_consumes_iteration_before_measurement`・`test_pair_pegasus_reused_identity_keeps_one_shot_claim` | 子 process が `from orchestrator.tests import test_campaign` で `ModuleNotFoundError: No module named 'skiputil'` (test_campaign.py:87)。`skiputil` は `orchestrator/tests/skiputil.py` で、pytest 下でだけ import 経路に入る。子の `PYTHONPATH` は repo root だけ | real・自分起因 (この wave の新 test) | fix-2: 子の `PYTHONPATH` に `orchestrator/tests` を足す (test 側) |
| R10 | `test_p3_exploration_namespace.py::test_driver_ast_supplements_runtime_namespace_gate[p3_s4_loop_policy]` | 方策 driver の `exploration_campaign_layout` 呼出し箇所の AST 棚卸し pin (`ast_layout_calls=2`) に対し、main の pair 分岐に 3 本目を足した | real・自分起因 | fix-2: 既存 test の期待値は変えない。main の pair 分岐で既存 helper `_campaign_layout(measurement_cfg)` を使い、呼出し箇所を 2 本のままにする (helper は同じ式 `exploration_campaign_layout(str(ident.campaign_id(cfg)))`) |

受理・拒否の含意: R9 は test の子 process の import 経路だけを直し、driver の受理集合を変えない。通る正例 = 子が実 `acquire_claim` まで到達する T1。R10 は同じ layout を同じ式で作るだけで、計測 layout の値・claim・受理集合を変えない。通る正例 = namespace inventory の 2 本の呼出し箇所と、T1 の計測 dir が `ident.campaign_id(計測 cfg)` と一致すること。
