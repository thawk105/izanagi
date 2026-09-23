U-B の 5 ファイルを実装しました。**試験は dispatch 障害で未実走のため、完了・GO とは判定していません。**

## 総括

- 生成器、5 arm の系列制御、初期点、参照分類、K0 handshake、費用、欠測優先順位付き集約を追加しました。
- 追加行数は **production 967 行／test 576 行**。所有外ファイル、B-5、既存テストの期待値は変更していません。commit は未作成です。
- 受理集合の追加は新 harness の CLI・名前空間・参照 genome。既存評価入口の変更は U-A に委ねています。
- AST 解析、module import、`check_docs.py` は成功。perf predicate discovery は新規両 module とも対象外でした。

試行したコマンドは以下です。**pytest 起動前に `qstat -Q preflight rc=1`、runner rc=16 で停止**しました。変異試験も未実走です。

```bash
PYTHONPATH=. python3 tools/run_tests.py -q \
  orchestrator/tests/test_t2849_generators.py \
  orchestrator/tests/test_t2849_comparison_harness.py \
  orchestrator/tests/test_t2849_comparison_aggregate.py \
  orchestrator/tests/test_p3_exploration_namespace.py \
  orchestrator/tests/test_official_perf_closure.py \
  orchestrator/tests/test_b5_generator_contrast.py \
  orchestrator/tests/test_plain_runner_coverage.py \
  orchestrator/tests/test_ccbench_spawn_sites.py
```

所有外への波及は、U-A の評価 CLI、U-C の job body／巡 tool の handshake consumer、上記既存回帰・メタテストです。共有 fixture の変更はありません。

**所有外の必要変更:** `check_codex_agents.py` は coder 役割定義の SHA drift で停止しました。[review_ledger.py:27](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2849-unit-b/orchestrator/codex_roles/review_ledger.py:27) 等の pin 更新が必要です。裁定上 U-C の担当なので編集していません。

変異対応表の `G/H/A` は、それぞれ `orchestrator/tests/test_t2849_{generators,comparison_harness,comparison_aggregate}.py` を表します。以下は**実装した検出先であり、kill 未確認**です。

| 変異 | 対象関数 | test nodeid |
|---|---|---|
| M8 | `_execute_slot`／`run_series` | H::test_initial_outside_b |
| M9 | `_execute_slot` | H::test_retry_counts_b_once |
| M10 | `BOGenerator.tell` | G::test_bo_excludes_candidate_failures |
| M11 | `gp_posterior`／`matern52` | G::test_gp_two_point_independent_values |
| M12 | `gp_posterior`／`expected_improvement` | G::test_ei_latent_variance |
| M13 | `EvolutionGenerator.tell` | G::test_equal_fitness_keeps_parent |
| M14 | `run_series` | H::test_initial_can_be_endpoint |
| M15 | `_disqualified`／`aggregate` | A::test_cross_series_disqualification |
| M16 | `aggregate` | A::test_missingness_precedence |
| M17 | `expected_inputs` | H::test_k0_uses_latest_normal |
| M18 | `classify_reference_slot` | H::test_reference_genome_mismatch_not_certified |
| M19 | `_execute_slot` | H::test_n_eval_independent_of_reps |
| M20 | `slot_argv` | H::test_llm_slot_argv_k0 |
| M21 | `run_series`／`expected_inputs` | H::test_rejection_does_not_advance_whiteboard |
| M22 | `_handshake` | H::test_role_costs_recorded |