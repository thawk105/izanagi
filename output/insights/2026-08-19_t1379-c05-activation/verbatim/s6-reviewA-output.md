## 総括

判定は **NO-GO**。C05のactivation、6件のfunction pin、g9の凍結hashは整合しているが、段4で登録した変異#2は `required_calls` まで含めると実効的に殺せない。

### must-fix

- `orchestrator/campaign/s8c_preregistration_evidence.py:1666-1681` の `required_calls` と `:1722-1734` の `required_targets` が冗長です。fixture (`orchestrator/tests/test_s8c_preregistration_predicates.py:909-931`) は `consume_schedule(...)` を1箇所だけ `return artifact` に置換しており、主に最終 `required_targets` 検査を検証しています。
  
  例えば `required_calls["consume_schedule"]` の `{"verify_schedule"}` 検査だけを弱めても、mutated supervisor では `consume_schedule` と `verify_schedule` が到達不能なままなので、`required_targets` が `UNSATISFIED / schedule-consumer-unreachable` を返します。したがってテストは緑になり、その `required_calls` 変異は SURVIVED です。

  変異登録を `required_targets` の単独変異へ狭めるか、supervisorから `consume_schedule` は呼ぶが consumer内部の `verify_schedule` edgeだけを欠落させる別fixtureを追加してください。

### nit

- `validate_condition_freeze_at` (`orchestrator/campaign/s8c_preregistration.py:1526-1643`) 自体はruntimeの `DECIDER_VERSION` とg9を比較しません。v4据え置き変異は `test_s8c_preregistration_invariant.py:398-426` と activation の `:1865-1877` で拒否されるためfail-closedですが、「凍結妥当性検査でreject」という裁定文は、正確には「activation/version bindingでreject」です。
- `nc_c05_initial_state_hash_bitflip` (`test_s8c_preregistration_predicates.py:909-931`) のpredicate用変異はhash bit flipではなくconsumer呼出し削除です。実際のbit flipは別テスト (`:2773-2813`) なので、変異台帳上の名称が混同を招きます。

### 確認できた点

- 契約反転・registry登録除去は `test_machine_checkable_contract_and_evaluator_registry_are_bijective` (`:2846-2856`) で単独なら検出できます。
- C05のfunction pinは契約 (`...contract.v1.json:190-228`) に対し、checked 2件 (`...invariant.py:78-79`)、excluded 4件 (`:114-117`)、missing 0件で過不足ありません。
- `.py`以外のmachine-checkable pathは現状C05のschedule artifactだけです。C03/C06/C08の非`.py` pathは `machine_checkable=false` なので今回の緩和の影響を受けません。
- g9 (`condition-freeze.v1.g9.json:1`) は契約hash `a40f...b17b5a6`、DECIDER v5、§5/§6/normative/protected hash、g8の `supersedes` を実bytesから再計算した値と一致しました。control用3 hashも再計算一致です。

pytestはread-only制約どおり実走していません。