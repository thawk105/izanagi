U-B 所有の3ファイルを修正しました。**実装済み・未実走のため、担当所見はすべて partial** です。commit は作成していません。

| 所見 | 状態 | 修正内容 |
|---|---|---|
| T4 | partial | critic fixture を正しい4見出しへ修正。key 欠落を拒否する既存期待値は維持 |
| T5 | partial | `SeriesLedger.append` で入れ子の値をコピーし、後続の timing 更新が保存済み event に波及する問題を修正 |
| A-R1 / M26 | partial | 参照分類で `src_token == source_digest.STOCK` を要求。全 workload に別 source の負例を追加 |
| A-R2 / M12 | partial | `test_ei_latent_variance` に実際の `BOGenerator.ask` 経路を追加。実 EI を呼びつつ独立計算と照合 |
| A-R3 / M18 | partial | sidecar・variant は一致し、WAL build genome だけ異なる負例を名指し試験へ追加 |
| A-R4 | partial | sweep 順序を初回の計時内で生成。初回だけ費用が加算され、集約にも残る試験を追加 |

受理集合の変更は、別 source の参照を certified にしない点です。exact genome・STOCK source・正常な verify/bench が揃う正例は維持しています。その他は fixture、台帳の再構成、費用計上、試験の検出力の修正です。

実走した nodeid は **0件**。次のコマンドは起動前に拒否されました。

```bash
PYTHONPATH=. timeout 300 python3 -m pytest -q -p no:cacheprovider -rf orchestrator/tests/test_t2849_generators.py orchestrator/tests/test_t2849_comparison_harness.py orchestrator/tests/test_t2849_comparison_aggregate.py
```

3ファイルの AST 構文確認と `git diff --check` は成功しました。所有外への静的な波及先は、driver を起動する `tools/pegasus/p3_s4_loop_pegasus.sh:711` と、その argv を検査する `test_t2849_job_contract.py` です。共有 fixture の consumer は `test_t2849_comparison_aggregate.py`。インターフェース変更・所有外の必要変更はありません。新規ファイルもありません。

## 総括

今回の差分は production **+7/-3行**、test **+58/-2行**。台帳・参照分類・sweep 計時を修正し、担当試験を補強しました。機能試験と変異 kill は親の再走待ちです。

以下は U-B の変異対応表です。**変異注入・FAIL の実測は未実施**です。H/G/A はそれぞれ `orchestrator/tests/test_t2849_comparison_harness.py`、`test_t2849_generators.py`、`test_t2849_comparison_aggregate.py` を表します。

| 変異 | 対象関数 | kill 期待 nodeid |
|---|---|---|
| M8 | `run_series` | H::test_initial_outside_b |
| M9 | `_execute_slot` | H::test_retry_counts_b_once |
| M10 | `BOGenerator.tell` | G::test_bo_excludes_candidate_failures |
| M11 | `_fit` / `gp_posterior` | G::test_gp_two_point_independent_values |
| M12 | `BOGenerator.ask` の EI 呼出し | G::test_ei_latent_variance |
| M13 | `EvolutionGenerator.tell` | G::test_equal_fitness_keeps_parent |
| M14 | `run_series` の endpoint 選択 | H::test_initial_can_be_endpoint |
| M15 | `_disqualified` | A::test_cross_series_disqualification |
| M16 | `aggregate` | A::test_missingness_precedence |
| M17 | `expected_inputs` | H::test_k0_uses_latest_normal |
| M18 | `classify_reference_slot` の WAL genome 照合 | H::test_reference_genome_mismatch_not_certified |
| M19 | `_execute_slot` | H::test_n_eval_independent_of_reps |
| M20 | `slot_argv` | H::test_llm_slot_argv_k0 |
| M21 | `run_series` の whiteboard 作成 | H::test_rejection_does_not_advance_whiteboard |
| M22 | `_handshake` | H::test_role_costs_recorded |
| M26 | `classify_reference_slot` の STOCK 照合 | H::test_reference_nonstock_source_not_certified |

実行を止めたのは PreToolUse の `guard_bash` です。「Pegasus ログインノードでの pytest 実行」を拒否しました。共通指示の「直接実行も拒否されたら実装済み・未実走と書く」に従い、迂回実行していません。