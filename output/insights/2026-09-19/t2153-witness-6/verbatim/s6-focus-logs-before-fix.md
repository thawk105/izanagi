# 親の焦点走 (author-impl.patch を wave worktree に展開した状態、`tools/run_tests.py <files> -q -rf`、Pegasus 計算ノードへ dispatch)

## 焦点走 1 (22:22、request 10764.nqsv、Elapse 11 s、pytest 6.00 s) — rc=1
対象: `orchestrator/tests/test_condition_meaning_gate.py`、`test_silo_ladder_rung1_driver.py`、`test_s1_direct_comparison.py`
結果: **2 failed, 371 passed**
- FAILED `test_condition_meaning_gate.py::test_report_companion_argv_establishes_report_only[False]`
- FAILED `test_condition_meaning_gate.py::test_report_companion_argv_establishes_report_only[True]`
- assert 位置 1064 行 `assert supply.terminal_status == meaning.terminal_status == "green"` → `'red' == 'green'`。
- 親が同じ手順を python で再現: **supply red `preprocess-output-empty`** ("owner TU preprocessing produced no bytes")、meaning は green。原因 = REPORT の toy fixture の所有 TU `cc/silo/ycsb_silo.cc` が `#if … / int … / #endif` だけで、既定 0 (companion 1 && REPORT 0) では `-E -P` の出力が 0 byte になり supply 側の防壁に当たる。実 `ycsb_silo.cc` は無条件の本文を持つので fixture の代表性の問題 (F29 型)。fixture に無条件の 1 行 (例: `int izanagi_owner_present = 1;`) を足すのが最小修正の候補。
- 他の新規 test (`test_sort_real_structure_establishes_only_branch_selection[False/True]`、`test_sort_undef_rejects_family_with_supply_still_green`、`test_report_missing_compile_argv_companion_rejects_meaning`、非対値 ×12、`test_real_s1_sort_request_establishes_meaning`、rung1 driver pin、docstring 17) は passed。

## 焦点走 2 (22:24、Elapse 351 s、pytest 344.57 s) — rc=0
対象: `test_p3_exploration_namespace.py`、`test_p3_build_authority_cli.py`、`test_sort_swo_oracle.py`、`test_s8b_oracle_driver.py`、`test_s8b_floor_campaign.py`、`test_p3_s4_loop_sort.py`、`test_s6_sort_sweep.py`
結果: **925 passed, 9 skipped** (赤なし)。所要の内訳は未計測 (増分の評価は別途)。

## probe (段 5 (i)) の結果は probe-result-summary.md。
