## 総括

D1–D4 を実装しました。commit、docs 編集、期待 matrix・採否規則・production の受理条件変更は行っていません。

- 12 負例の baseline/prototype と POS-1 baseline は 1 block。
- POS-1 prototype は候補ごとに 201 block を 1 回、計 3 回。
- 重い比較走と候補別非後退走を pytest collection から測定 harness へ移動。
- 候補単位の shard、39 組完全性検査、canonical `comparison.json` 合成を追加。
- 記録済み `comparison.json` を再導出検査する fail-closed pytest node を追加。
- 現在 `comparison.json` は未生成なので、当該 node は親の測定完了まで意図どおり赤です。

主要箇所は [experiment module](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/orchestrator/campaign/p3_b4_producer_auth_experiment.py:640)、[measurement harness/test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:1309)、[prereg](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/output/insights/2026-09-03_t2103-producer-auth-layer/mutation-prereg.json) です。

## 所見ごとの対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| D1 | partial | 1-block fixture、実 route、exact layer/reason 照合、期待不一致時の shard rc=1 と合成拒否を実装。全 12 負例の実測は infrastructure failure により未実走。 |
| D2 | partial | POS-1 baseline=1、prototype=201 を prereg に固定。候補 shard 1 回につき 201-block positive は 1 回だけ。計 3 回の実測は親待ち。 |
| D3 | closed | 78-phase 比較 node と候補別 29-node 非後退 nodeを pytest collection から除き、同じ処理を harness へ移動。39 組と decision を記録から再導出する node を追加。 |
| D4 | closed | `measure-candidate --candidate` と `combine --shard` を実装。3 候補、同一 base commit、39 組、期待理由、非後退結果が揃わなければ decision を出力しない。CLI surface は確認済み。 |

## 最小 block 数と根拠

最小値は **1 block** です。

- 1 manifest row が on/off の両 arm を持つため、on/off pair が成立。
- その 1 block で両 arm の terminal record を実生成。
- 2 source artifact と raw record を production publisher/assembler が処理し、source evidence 再導出が発火。
- R 系は first on-arm artifact の実体を書き換え、`evidence_binding:source_rederivation` への到達を要求。
- frozen prototype は evaluator 前に closure receipt を生成。closure 自体は production の 201-block 契約で検証し、その後、使い捨て process 内だけ evaluator の期待 block 数を 1 に設定。
- evaluator result が欠落または `analysis_invalid` の場合は accepted にせず既存 gate rejection として記録。
- guard 負例は正確に `producer_auth_mismatch`、R 系は正確に `evidence_binding:source_rederivation` へ到達しなければ shard 合成を拒否。

POS-1 prototype のみ 201 block を維持します。

## 測定 harness の起動方法

以下の 3 コマンドは候補単位であり、別々の計算ノードへ並列投入できます。出力先は新規 file である必要があります。

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate issuer \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/issuer \
  --output /work/1/SFC/tanab/t2103-scratch/shards/issuer.json
```

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate raw_assembly \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/raw \
  --output /work/1/SFC/tanab/t2103-scratch/shards/raw.json
```

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate temporary_6_member_expanded_closure_prototype \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/frozen \
  --output /work/1/SFC/tanab/t2103-scratch/shards/frozen.json
```

3 shard がすべて rc=0 になった後に合成します。

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py combine \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/issuer.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/raw.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/frozen.json \
  --output output/insights/2026-09-03_t2103-producer-auth-layer/comparison.json
```

各 shard は 25 回の 1-block phase、1 回の 201-block POS-1 prototype、候補有効状態の非後退走を実行します。

## pytest に残した node

合計は parametrization 展開後 42 node の想定です。所要は未実測の静的見積もりです。

| 分類 | node | 想定所要 |
|---|---|---|
| pure/static gate | `test_expected_matrix_has_twelve_negative_cases_and_pos_1`、`test_rogue_producer_is_a_separate_implementation_path`、`test_measurement_harness_routes_cases_through_real_probe`、`test_c1_preregistration_requires_two_processes`、`test_comparison_report_is_canonical_and_has_no_volatile_payload`、`test_wave_mutation_node_mapping_is_complete_and_one_to_one`、W02、W03、W05–W08、decision fail-closed 4 variants、非後退 decision、missing prereg、candidate shard completeness、recorded comparison | 各 1 秒未満目安 |
| scratch/meta | 主 worktree 不変、scratch root、runtime HEAD pin、rogue artifact 3 variants、prototype anchor、real callsite、frozen evaluator ordering、W01、W04、W09、disposable mutation | 各 1–8 秒目安 |
| W calibration | `test_wave_mutant_kills_exactly_one_registered_node[w01-w08]` | 各 3–12 秒、計 24–96 秒目安 |
| case-local abort | `test_case_failure_records_aborted_and_remaining_cases_continue` | 20–60 秒目安 |

全体は 5 分以内を想定していますが、正式実測は未完了です。

pytest から外した重い node は、旧 `test_full_baseline_and_prototype_comparison_in_external_scratch` と `test_candidate_enabled_producer_29_node_non_regression[...]` です。処理は削除せず harness に移しています。

## 実走した node と結果

pytest で実際に開始できた node はありません。

最終コードに対して軽量 8 node を `tools/run_tests.py` 経由で投入しましたが、結果は以下でした。

- rc=16
- `qstat -Q preflight rc=1`
- `child_started=false`
- test failure なし。ただし test process 未起動のため緑とは報告しません。

投入した 8 node は期待 matrix、実 route 配線、C1 prereg、canonical report、W mapping、W08、W09、39-pair shard completeness です。すべて実装済み・未実走です。

pytest 外の静的確認結果:

- Python AST parse: 通過
- prereg v4 の内容再導出完全一致: 通過
- W01–W08 exact anchor 出現数: 全件 1
- 全 prototype patch anchor 出現数: 全件 1
- `git diff --check`: 通過
- `measure-candidate --help` / `combine --help`: rc=0
- 重い候補 shard、201-block POS-1、候補別非後退走: 実装済み・未実走

## 受理・拒否挙動の変更点

**変えていない。**

期待 matrix、6 件の採否入力、tie-break、凍結 reason enum、production の受理集合は不変です。変更したのは fixture scale、測定の配置、shard 合成条件、記録済み成果物の fail-closed 検査だけです。

## 従えなかった項目

実装上、従えなかった項目はありません。commit、docs 編集、skip、期待値変更、恒久 pin 拡張は行っていません。

未完了なのは infrastructure failure による pytest と測定 harness の実走だけです。親による 3 candidate shard と合成後、記録済み `comparison.json` gate を含む全 pytest を実行する必要があります。