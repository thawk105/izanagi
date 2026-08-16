# 親の実測ログ (2026-08-16 07:49〜08:25 JST)

対象 commit: worktree HEAD = local main `10813338`
repo: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-t1134-prereg-contract`

## M1. 契約の現状

`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` の 12 条件すべてが
`"machine_checkable": false`。`_MACHINE_EVALUATORS` に実装があるのは 6 条件
(1, 4, 9, 10, 11, 12)。`PredicateRegistry.evaluate_all` は `machine_checkable` が false のとき
`_evaluate_undefined` へ落とすため、6 本は 1 本も呼ばれない。

## M2. 6 評価器を強制発火させた実測

契約を読み込んだうえで `_ConditionProbe` を直接組み、各 `_evaluate_cNN` を HEAD に対して呼んだ結果。

```
C01  UNSATISFIED  workload-projection-mismatch
C04  UNSATISFIED  crash-policy-cell-partial
C09  UNSATISFIED  formal-acceptance-layer3-consumer-absent
C10  UNSATISFIED  cross-binding-verifier-incomplete
C11  UNSATISFIED  sample-plan-absent
C12  UNSATISFIED  environment-contract-consumer-absent
```

**全件 UNSATISFIED であり、終端の `EVIDENCE_UNDEFINED` には 1 本も到達しない。**
したがって `machine_checkable` を true へ反転しても、受理集合は 1 bit も広がらない
(充足 0 のまま)。変わるのは診断の粒度だけである。

## M3. 終端の構造

6 本の評価器はいずれも、すべての検査を通過した先で
`core.PredicateStatus.EVIDENCE_UNDEFINED` と
`ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE` を返す
(`s8c_preregistration_evidence.py` の各 `_evaluate_cNN` 末尾)。
`SATISFIABLE_CONDITION_IDS` は `frozenset()` (空)。

## M4. 条件 11 の「既存 4 機構」の実在確認

`orchestrator/campaign/p3_autonomous_workload_trial.py` に対する実測。

```
MAX_APPROVED_GENERATIONS = 2            (>= 2: True)   L122
_validate_generation_budget 定義         L389
  main            が呼ぶ  True           L3233
  run_trial       が呼ぶ  True           L2778
  _run_workload   が呼ぶ  True           L2332
apply_critic_feedback を _run_workload が呼ぶ  True     L2436
_role_metric_payloads 定義               L1013
_run_workload 内に "sample_plan_sha256"/"cap_lift_sha256" の文字列  False
```

`_evaluate_c11` の検査順は 世代上限 → 3 入口 validator → critic feedback →
sample_plan artifact → cap_lift artifact → 文字列束縛。
**先頭 3 つは通る。落ちているのは sample_plan 以降だけ。**
したがって sample_plan / cap_lift を証拠から外すと、C11 は残る検査を全通過し
終端 (`EVIDENCE_UNDEFINED`) へ到達する。

作らないと裁定済みの 2 件 = `output/s8c-preregistration/sample-plan.v1.json`、
`output/s8c-preregistration/generation-cap-lift.v1.json`。どちらも repo に存在しない。

## M5. D96 手続の世代記録と D 採番の順序衝突

- `condition-freeze.v1.g2.json` の `ruling_reference` は `"D410"`。g1 は `null`
  (`_assert_rulings_exist` は generation 2 以上にだけ ruling を要求する)。
- `_assert_rulings_exist` (`s8c_preregistration.py` L1352〜L1374) は、
  `docs/decisions.md` に `^## D<N>\.` の見出しが **記録を導入した commit の時点で**
  実在することを要求する。
- 実測した前後関係:
  - g2 の導入 commit `d0fc008c` (2026-08-15 23:32)
  - D410 が着地した commit `94ce4ccf` (2026-08-15 11:12, "Fold landed documentation fragments")
  - `git merge-base --is-ancestor 94ce4ccf d0fc008c` → rc=0 (**D410 が先に着地している**)
- `validate_condition_freeze_at(ROOT, 'HEAD')` は現状 rc=0、generation 2 を返す。
- 受入テスト `orchestrator/tests/test_s8c_preregistration_invariant.py` L131 は
  作業ツリーから候補 commit を合成して `validate_condition_freeze_at` を実検査する。
  したがって D が未着地のまま g3 を書くと受入が赤になる。

## M6. D96 (2) が要求する境界テスト

`orchestrator/tests/test_s8c_preregistration_predicates.py`

- L499 `test_satisfiable_predicate_requires_negative_control`
- L506 `assert machine_checkable == M.SATISFIABLE_CONDITION_IDS == frozenset()`
- L488 `NEGATIVE_CONTROL_CASES` に 6 条件分の negative control が登録済み
  (`nc_c01_perf_scale_regression` → C01 など)

## M7. pin 閉包 (DW-O09)

`s8c_preregistration_evidence_contract` / `phase3-8c-preregistration` / `condition-freeze` /
`s8c_preregistration_evidence` を `*.py` `*.json` `*.md` `*.toml` `*.cfg` 全件検索した結果のうち、
歴史記録 (`output/insights/**`, `docs/archive/**`) を除いた生きた pin:

```
orchestrator/campaign/s8c_preregistration.py                (7 hit)
orchestrator/tests/test_s8c_preregistration_invariant.py    (2 hit)
orchestrator/tests/test_s8c_preregistration_core.py         (1 hit)
orchestrator/tests/test_s8c_preregistration_predicates.py   (1 hit)
tools/check_docs.py:64   prereg doc を「発効前は living」として登録 (exact pin なし)
docs/decisions.md                                           (6 hit)
docs/phase3-8c-preregistration.md                           (3 hit)
docs/README.md / docs/phase3-s8c-autonomous-trial-runbook.md / output/README.md
output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1.json / .g2.json
```

`SATISFIABLE_CONDITION_IDS` を key に張った pin は
`test_s8c_preregistration_predicates.py:506` の 1 件のみ。
`PREDICATE_IDS` は `s8c_preregistration.py` と 3 test file が参照。

## M8. 稼働 wave との編集面重複

t1112-8c-live-abc / t523-holdout-admission / t257-land-lock-wait /
t1049-replay-cache-isolation の 4 本を実測。8c 事前登録系ファイルとの重複はゼロ。
