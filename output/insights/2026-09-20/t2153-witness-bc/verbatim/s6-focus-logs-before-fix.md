# 親の実走 log 要約 (段 5 patch 展開後、wave worktree、2026-09-20 14:30〜14:36 JST)

## 焦点走 1 (所有 test 3 file、計算ノード generic dispatch、Elapse 12 s、pytest 6.60 s)
`python3 tools/run_tests.py orchestrator/tests/test_condition_meaning_gate.py orchestrator/tests/test_s8a_trigger_sweep.py orchestrator/tests/test_silo_ladder_rung1_driver.py -q -rf`
→ **302 passed / 1 failed**。赤 = `test_condition_meaning_gate.py::test_module_claim_names_the_exact_38_define_supply_domain` (module docstring の逐語 pin: "registered macros plus five mocc controls additionally have a bounded" / "compile-time witness (18 total)" を要求。author が docstring を "Twenty-one registered macros additionally have a bounded compile-time witness" に変えたが、この pin test を追随していない)。原本: job dir `focus-own1.log`。

## 焦点走 2 (consumer 18 file、計算ノード、Elapse 109 s、pytest 102.92 s)
file: test_build_site_gate, test_ccbench_spawn_sites, test_mocc_mutation_proof, test_mocc_proof_surface, test_mocc_template_proof, test_p3_build_authority_cli, test_p3_exploration_namespace, test_p3_s4_loop, test_p3_s4_loop_sort, test_p3_s4_loop_trigger_gating, test_paper_story_a2_certification, test_pegasus_calibration_workload, test_s1_direct_comparison, test_s1_verify_extime_calibration, test_s5_permutation_coverage, test_t152_write_intent_coverage, test_t316_sandbox_probe, test_p3_b4_wiring_probe
→ **1695 passed / 45 failed / 2 skipped**。内訳:
- 44 件 = `test_s1_direct_comparison.py` (`test_prepare_accepts_all_32_canonical_predicates` ×32、`test_prepare_accepts_six_frozen_gate_predicates` ×6、`test_prepare_system_gate_passes_predicate_verbatim_to_quarantine` ×3、`test_prepare_ident_all_passes_predicate_verbatim_to_quarantine` ×2、`test_promotion_contract_carries_unestablished_meaning_macro` ×1)。原因は 1 つ: S1 test の fixture helper `_materialize_requested_condition_macros` (test_s1_direct_comparison.py 697-732) が要求 macro ごとに **`#if <MACRO>` 箇所を 1 つだけ** owner TU 末尾へ足す。`BACKOFF_TRIGGER_GATING` が N=12 で登録されたため、S1 の実 evaluator 経路 (`_condition_records_for_genome` → factory) で `compile-time-branch-site-count-mismatch` (expected 12 / observed 1) → family reject → `DriverError`。`test_promotion_contract_carries_unestablished_meaning_macro` (794-804) は GATING 1/0 を「未確立が admission に持ち越される」例に使っており、GATING が witness を得た今、実 request では成立しない (S1 が要求しうる 4 macro = FIXED / NOINLINE / TRIGGER_GATING / SORT はすべて witness 付き)。
- 1 件 = `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` = `git status --short` が probe 2 file 以外の変更を許さない test。wave worktree に段 5 patch が未 commit で展開されているため赤 (実装の欠陥ではなく統合 commit 後に再走する)。
原本: job dir `focus-cons1.log`。

## 実 TU cell (login pegasus02、patched production module、official 同形供給、`login-after/`、変更前は `login-before/` `login-before2/`)
| cell (木 / macro / 要求 vs 対照) | supply | meaning | admission |
|---|---|---|---|
| gating-instr (skeleton+instr = coverage 第 1 腕) / BACKOFF_TRIGGER_GATING / 1 vs 0 | green | **green (12,12)/(0,12)** | admitted、未確立 [] |
| gating-misattr (skeleton+instr+misattr = coverage 第 2 腕) / BACKOFF_TRIGGER_GATING / 1 vs 0 | green | **green (12,12)/(0,12)** | admitted、未確立 [] |
| gating-misattr / IZANAGI_BREAK_TRIGGER_MISATTR / 1 vs 未定義 | green | **green (1,1)/(0,1)** (default define_value = null) | admitted、未確立 [] |
| gating-misattr / IZANAGI_BREAK_TRIGGER_MISATTR / 1 vs 0 | red `preprocess-bytes-identical` | unestablished (factory None) | rejected (設計どおり) |
| rung1 / IZANAGI_SILO_LADDER_RUNG1 / 1 vs 0 | green | **green (2,2)/(0,2)** | admitted、未確立 [] |
| sort / SORT_VARIANT / 1 vs 0 (既存) | green | green (1,1)/(0,1) | admitted |
| rung1 / IZANAGI_SILO_LADDER_RUNG1_REPORT / 1 vs 0 (既存、companion RUNG1=1) | green | green (1,1)/(0,1) | admitted |
configure: MISATTR / GATING は s8a genome (`BACK_OFF=1 NO_WAIT_LOCKING_IN_VALIDATION=1 NO_WAIT_OF_TICTOC=0 WAL=0 BACKOFF_TRIGGER_GATING=1 ADD_ANALYSIS=1 TRACE=1`) + 供給 4 引数、他は供給 4 引数のみ。g++ 11.4.0 / cmake 3.22.1。

## I1 (既存 macro の変更前後)
SORT / REPORT の record (supply・meaning・admission) を変更前 (`login-before2`) と変更後 (`login-after`、同 driver-id) で leaf 単位に比較: 異なる leaf は一時 path (`/tmp/izanagi_condition_supply_*`、`/tmp/izanagi_compile_time_branch_*`) を含む argv とそれに派生する `record_digest` / `record_id` / `admission_digest` / `record_ids` だけ。key 集合・前処理 digest・byte 数・owner TU sha・dependency closure digest・counts・define_value・reason・proof_kind は同一。
登録前後の supply (新規 3 macro): MISATTR / RUNG1 (CXX_FLAGS route) は登録により共有 build root へ移行 (control root が `default` → `requested`)、GATING (cache route) は分離のまま。4 cell とも前処理 digest・bytes・owner TU sha・dependency closure digest が登録前後で一致。
