# 段 4 追補裁定 2 — 新 macro 登録に従属する共有 fixture と件数 (2026-09-30)

発端: 親の焦点走 f1 (5120a367a、計算ノード、7 failed / 1757 passed / 5 skipped、log = job dir focus-run-f1.log) の赤 7 件。

## 帰属

| nodeid | assertion | 帰属 |
|---|---|---|
| test_condition_meaning_gate.py::test_compile_time_branch_selection_accepts_each_registry_macro[SILO_ORDER_VARIANT] | ('red','configure-failed') | 共有 fixture `orchestrator/tests/condition_gate_test_support.py` の `_OPTIONS` (fixture 用 Options.cmake) が登録 macro を列挙しており、`CCBENCH_SILO_ORDER_VARIANT` の CACHE 行と universal definitions の行が無いため fixture の configure が失敗 (SILO_POLICY_VARIANT は 26・39 行にある) |
| 同 ::test_new_branch_selection_supply_meaning_and_admission[SILO_ORDER_VARIANT] | 'red' == 'green' | 同上 |
| 同 ::test_new_branch_green_schema_rejects_count_value_and_argv_mutations[SILO_ORDER_VARIANT] | 'red' == 'green' | 同上 |
| 同 ::test_v1_domain_and_claim_boundaries_are_exact | `sum(route == ROUTE_CMAKE_CACHE) == 24` が 25 | 新 macro は CMake cache 経由 (段 4 で許可) |
| test_ccbench_spawn_sites.py::test_define_sink_cross_product_classifies_t2155_production_sinks_exactly | s1 sink の proven-unreachable 71 が 72 | patch 由来の define が 1 つ増え、s1 sink はこの patch を当てないので到達不能が 1 つ増える |
| 同 ::test_ro_gc_publish_build_sink_uses_complete_condition_gate_family | proven-unreachable 71 が 72 | 同上 |
| 同 ::test_define_sink_cross_product_t2520_certify_entry_removal | proven-unreachable 61 が 62 | 同上 |

いずれも段 4 で許可した「SILO_ORDER_VARIANT を条件意味 gate の supply domain へ 1 つ登録する」ことの直接の帰結で、実装 (patch・gate 本体) の誤りではない。段 4 と追補 1 で従属箇所を列挙し漏れた。

## 許可する変更 (これ以外の既存期待値は変えない)

1. `orchestrator/tests/condition_gate_test_support.py` の `_OPTIONS` に、SILO_POLICY_VARIANT の 2 行と同じ形で `set(CCBENCH_SILO_ORDER_VARIANT 0 CACHE STRING "...")` と universal definitions の `SILO_ORDER_VARIANT=${CCBENCH_SILO_ORDER_VARIANT}` を **追記** する。
2. test_condition_meaning_gate.py の `== 24` (ROUTE_CMAKE_CACHE の数) → 25。
3. test_ccbench_spawn_sites.py の proven-unreachable 71 → 72 (2 か所)、61 → 62 (1 か所)。
4. 3 を直した後に同じ test の後段で現れる、同じ理由 (patch 由来の define が 1 つ増えた) による件数の +1 (例: s8b sink の `covered: 75`)。**この 4 に当たる変更は、各 1 行ごとに「どの sink から見てこの macro が covered / unreachable / deferred のどれか」を現物のコードで示してから行う**。+1 以外の変化、別の分類への移動、件数以外の期待の変化が出たら直さずに報告して止まる。

受理・拒否の含意: 受理集合の変化は段 4 で許可した SILO_ORDER_VARIANT の登録 1 つだけで、他の macro の受理・拒否と sink の分類は変わらない。通る正例: fixture の木で SILO_ORDER_VARIANT の compile-time 分岐 witness が 'green' (declared-compile-time-branch-selection-observed) になる。

並行 wave の注意: 同じ件数を並行 wave も +1 していれば、main 取り込み時に git が同値の書き換えを 1 回分に畳む。取り込み後に実数と照合する (追補 1 と同じ)。
