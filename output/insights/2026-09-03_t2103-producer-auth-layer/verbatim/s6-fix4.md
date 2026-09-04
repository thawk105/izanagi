## 総括

D9〜D11 と診断情報保持を実装しました。

- 測定経路だけが evaluator へ `floor=0` を供給します。material report の入力構築と production callsite は維持しています。
- `floor_domain_error` は `ENVIRONMENT_CONSTANT` として記録され、候補の拒否や KILLED / SURVIVED に計上されません。
- POS-1 baseline の accepted 必須条件と fail-closed を維持しました。
- `analysis_invalid.reasons` は省略せず shard JSON と stderr 診断へ出力します。
- report に floor に関する非保証を追加しました。
- prereg v6、report v6、shard v3 とし、evaluator 契約を明示しました。

変更箇所は [experiment module](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/orchestrator/campaign/p3_b4_producer_auth_experiment.py:45)、[measurement harness](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:340)、[prereg](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/output/insights/2026-09-03_t2103-producer-auth-layer/mutation-prereg.json) です。rogue support は本巡では変更していません。

commit、git add、stash、branch 操作、docs 編集は行っていません。

## 所見ごとの対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| D9 | closed | `_load_and_evaluate` を通したまま、その evaluator call だけを wrapper で `floor=None` から整数 `0` へ置換。baseline / prototype 共通経路。prereg と各 shard に evaluator 契約を記録。report に productionとの差を非保証として追加。 |
| D10 | closed | `CaseOutcome.ENVIRONMENT_CONSTANT` を追加。`floor_domain_error` を含む observation は `existing_gate_rejected=false` で記録し、shard の `classification` に明記。incremental kill は偽、decision は `environment_constant_present` で拒否。 |
| D11 | closed | POS-1 baseline が欠落または accepted 以外なら shard rc=1。combine でも accepted を要求し、理由を付けて停止。数字は生成しない。 |
| 診断情報 | closed | `analysis_invalid.reasons` 全件を `evaluator:analysis_invalid:reasons=...` に保存。floor の場合も同じ詳細を `ENVIRONMENT_CONSTANT:` の後ろに保持し、shard JSON と log の双方へ出力。 |

期待 matrix、採否規則、201 block、5-file pin、凍結 reason enum は変更していません。

## 6 shard の起動 command

前巡から command と combine argv は変わっていません。出力先は新規 file が必要です。

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate issuer \
  --phase baseline \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/issuer-baseline \
  --output /work/1/SFC/tanab/t2103-scratch/shards/issuer-baseline.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate issuer \
  --phase prototype \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/issuer-prototype \
  --output /work/1/SFC/tanab/t2103-scratch/shards/issuer-prototype.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate raw_assembly \
  --phase baseline \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/raw-baseline \
  --output /work/1/SFC/tanab/t2103-scratch/shards/raw-baseline.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate raw_assembly \
  --phase prototype \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/raw-prototype \
  --output /work/1/SFC/tanab/t2103-scratch/shards/raw-prototype.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate temporary_6_member_expanded_closure_prototype \
  --phase baseline \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/frozen-baseline \
  --output /work/1/SFC/tanab/t2103-scratch/shards/frozen-baseline.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate temporary_6_member_expanded_closure_prototype \
  --phase prototype \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/frozen-prototype \
  --output /work/1/SFC/tanab/t2103-scratch/shards/frozen-prototype.json
```

combine argv:

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

## 実走した node と結果

pytest node の実走完了はありません。最終コードに対して以下を `tools/run_tests.py` へ投入しました。

```text
test_expected_matrix_has_twelve_negative_cases_and_pos_1
test_frozen_prototype_uses_material_report_route_and_precedes_evaluator
test_measurement_harness_routes_cases_through_real_probe
test_measurement_supplies_floor_zero_at_the_material_report_evaluator
test_floor_domain_error_is_not_attributed_to_a_candidate
test_analysis_invalid_diagnostic_preserves_all_reasons
test_report_discloses_measurement_floor_non_guarantee
test_comparison_report_is_canonical_and_has_no_volatile_payload
test_w02_baseline_rejection_is_not_an_incremental_kill
test_w08_preregistration_is_rederived_from_content
test_w09_pos_1_is_accepted_by_every_candidate
test_decision_is_unavailable_for_incomplete_or_invalid_measurements
test_candidate_shards_require_all_39_pairs_before_decision
test_pos_1_baseline_must_reach_accepted_before_combination
```

結果は rc=16、`qstat -Q preflight rc=1`、`child_started=false` です。queue state も ENA / STS とも観測不能でした。全 node と6 shard 本走は実装済み・未実走です。

実走不能を補う静的・合成検証結果:

- Python AST parse: 通過
- subprocess probe script compile: 通過
- prereg と executable registry の完全一致: 通過
- synthetic 6 shard の canonical parse / combine: 通過
- `floor=0` evaluator 契約: 通過
- `ENVIRONMENT_CONSTANT` shard serialize / parse: 通過
- environment case の非計上と decision 拒否: 通過
- report 非保証: 通過
- `git diff --check`: 通過
- U+0300〜U+036F: 検出なし

## 受理・拒否挙動の変更点

production の受理・拒否挙動は変更していません。production は引き続き `floor=None` を渡し、権威ある floor 成果物が未発行のため `floor_domain_error` を返します。

測定 harness のみ次を変更しました。

- material report が構築した evaluator 引数のうち floor だけを `0` に置換。
- `floor_domain_error` を既存 gate の拒否から環境定数へ再分類。
- 環境定数を KILLED / SURVIVED / BASELINE_REJECTED のいずれにも計上せず、合成を拒否。
- POS-1 baseline 未到達時の停止を維持し、観測 reason と分類を出力。
- floor 以外の `analysis_invalid` も全 reasons を保持したまま既存 gate rejection として扱う。

## 従えなかった項目

pytest node と6 shard 本走は、Pegasus dispatch infrastructure failure により実行できませんでした。それ以外の指定事項には従っています。