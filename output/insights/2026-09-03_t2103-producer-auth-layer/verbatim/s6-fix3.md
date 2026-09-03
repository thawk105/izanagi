## 総括

D5-D8 を実装しました。主要変更は [experiment module](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/orchestrator/campaign/p3_b4_producer_auth_experiment.py:663)、[measurement harness](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:1351)、[prereg v5](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/output/insights/2026-09-03_t2103-producer-auth-layer/mutation-prereg.json) です。

- 全 case・両 phase を固定 201 block に変更。
- evaluator の期待 block 数を書き換える緩和を全廃。
- candidate x phase の 6 shard に分割。
- 各 shard に 13 phase の `wall_seconds` を記録。
- POS-1 baseline が accepted でなければ、理由付きで rc=1 とし、combine も拒否。
- 6 shard、39 pair、期待 route が揃わなければ decision を出力しない。
- commit、git add、stash、branch 操作、docs 編集はしていません。

## 所見ごとの対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| D5 | closed | `measurement_block_count` は登録済み全 mutation・両 phase へ常に 201 を返す。1-block 定数・経路と `EXPECTED_BLOCK_COUNT` 書換えを削除。baseline/prototype の経路引数も同一化。 |
| D6 | closed | `measure-candidate --phase {baseline,prototype}` を追加。shard schema は candidate x phase、combine は厳密に 6 shard と39 pairを要求。 |
| D7 | partial | POS-1 baseline accepted の shard rc=1／combine 拒否を実装し、合成データでは `evaluator:analysis_invalid` を理由付きで拒否することを確認。実 201-block route は infrastructure failure により未実走。 |
| D8 | closed | shard の各13 resultへ有限・非負の `wall_seconds` を記録し、canonical parseでも再検証。prototype non-regression の所要も記録。 |

## 6 shard の起動 command

出力先は新規 file である必要があります。

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate issuer \
  --phase baseline \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/issuer-baseline \
  --output /work/1/SFC/tanab/t2103-scratch/shards/issuer-baseline.json
```

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate issuer \
  --phase prototype \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/issuer-prototype \
  --output /work/1/SFC/tanab/t2103-scratch/shards/issuer-prototype.json
```

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate raw_assembly \
  --phase baseline \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/raw-baseline \
  --output /work/1/SFC/tanab/t2103-scratch/shards/raw-baseline.json
```

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate raw_assembly \
  --phase prototype \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/raw-prototype \
  --output /work/1/SFC/tanab/t2103-scratch/shards/raw-prototype.json
```

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate temporary_6_member_expanded_closure_prototype \
  --phase baseline \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/frozen-baseline \
  --output /work/1/SFC/tanab/t2103-scratch/shards/frozen-baseline.json
```

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate temporary_6_member_expanded_closure_prototype \
  --phase prototype \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/frozen-prototype \
  --output /work/1/SFC/tanab/t2103-scratch/shards/frozen-prototype.json
```

combine:

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py combine \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/issuer-baseline.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/issuer-prototype.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/raw-baseline.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/raw-prototype.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/frozen-baseline.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/frozen-prototype.json \
  --output output/insights/2026-09-03_t2103-producer-auth-layer/comparison.json
```

## 1 shard あたりの想定所要と根拠

1 shard は13件 x 201 blockです。

- T-2049 実測上限72秒 x 13件 = 936秒、約15.6分。
- prototype shard は候補別29-node非後退走が約29秒追加。
- scratch tree生成、process起動、C1のprocess分離を含め、実運用見積りは baseline 約16-19分、prototype 約17-20分。
- 3600秒を十分下回る見込みなので、変異族による追加分割は実装していません。

## 実走した node と結果

実走完了した pytest node はありません。以下10 nodeを `tools/run_tests.py` 経由で最終コードへ投入しましたが、2回とも rc=16でした。

```text
test_expected_matrix_has_twelve_negative_cases_and_pos_1
test_frozen_prototype_uses_material_report_route_and_precedes_evaluator
test_measurement_harness_routes_cases_through_real_probe
test_wave_mutation_node_mapping_is_complete_and_one_to_one
test_w02_baseline_rejection_is_not_an_incremental_kill
test_w08_preregistration_is_rederived_from_content
test_w09_pos_1_is_accepted_by_every_candidate
test_case_failure_records_aborted_and_remaining_cases_continue
test_candidate_shards_require_all_39_pairs_before_decision
test_pos_1_baseline_must_reach_accepted_before_combination
```

結果は `qstat -Q preflight rc=1`、`child_started=false` です。全 node は実装済み・未実走です。重い6 shardも実装済み・未実走です。

静的・合成検証では以下を確認しました。

- Python AST parse: 通過
- prereg v5 再導出完全一致: 通過
- prototype patchとtrust anchor: 3候補すべて通過
- W01-W08 exact anchor: 各1件
- 6 shard／39 pair合成: 通過
- 5 shardのみの合成: 拒否
- POS-1 baseline `analysis_invalid`: 理由付き拒否
- `git diff --check`: 通過
- CLI help: rc=0

## 受理・拒否挙動の変更点

production の受理・拒否挙動は変えていません。期待 matrix、採否規則、凍結 reason enum、5-file pinも不変です。

measurement harness では次を追加しました。

- POS-1 baseline が accepted でなければ shard rc=1。
- combine は6 shard欠落、POS-1 baseline拒否、route不一致を拒否し、decisionを生成しない。
- 前巡の期待不一致時 rc=1 と合成拒否は維持。

## 従えなかった項目

- 実201-block測定とpytest node実走は、Pegasus queue preflight失敗により実施できませんでした。
- 前巡で追加された harness自己検査の `1 block` 期待だけは、D5の「1-block経路を削除」と両立させるため201へ更新しました。既存production testの期待値、期待 matrix、採否規則は変更していません。