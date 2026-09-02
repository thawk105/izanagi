# 段 4 裁定のために親が待機中に足した実測 (M8〜M13)

## M8. supervisor は schedule module を一度も import していない

`grep -n "s8c_schedule\|load_schedule\|verify_schedule\|consume_schedule"
orchestrator/campaign/p3_autonomous_workload_trial.py` の hit は
`_load_s8c_schedule_authority` の定義 (`:1856`) と呼び出し (`:1894`) の 2 行だけ。
**C05 が要求する `run_trial -> load_schedule / verify_schedule / consume_schedule` の配線は
production に丸ごと存在しない。** したがって本 wave の配線は測れる純増である。

## M9. 現行の raise を固定するテストは無い

`test_p3_autonomous_workload_trial.py` で `_load_s8c_schedule_authority` に触れるのは `:9053` の
monkeypatch 1 箇所だけで、無条件 raise を期待値として pin するテストは無い。
**実装しても既存テストの期待値を変える必要は生じない。** `:9030-9075` の fixture は
`ReservationCell` / `BudgetLimits` を捏造して `_prepare_s8c_budget_inputs` の下流検査を試す。
新しいテストはこの monkeypatch を使わずに実解決経路そのものを通す必要がある。

## M10. initial-state 8 key のうち 2 件は production 権威が実在する

`s8c_generation_projection.ATTEMPT_POLICY` (`:27-31`) と `STOP_POLICY` (`:32-35`) は
`MappingProxyType` の実定数。18 key の語彙は role payload の閉 key 集合と同じ出所である。

## M11. C05 到達性の測り方 (段 6/7 で親が実測する)

`_evaluate_c05` は artifact 不在で第 1 分岐 (`schedule-schema-absent`) を返すため、
配線の効果は artifact を置かないと見えない。**本 wave の配線が本物なら、artifact を合成した木での
C05 は `schedule-consumer-unreachable` を抜けるはずである。** 段 2 の子は「メモリ上で実 evaluator と
production AST を使って確認し、現行は `UNSATISFIED / schedule-consumer-unreachable`、配線後は
`EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` になった」と報告している。
**この主張は親が段 6/7 で独立に実測して検算する。** artifact は repo へ commit しない。

## M12. 18 key authority のうち production 実値で落ちるのは whiteboard だけ (実測)

`s8c_schedule.validate_authority` へ、production の実値から射影した authority を渡した結果。

```
WHOLE: rejected -> authority value 'whiteboard' must not be an empty array
  arms OK / attempt_policy OK / baseline OK / descriptor_binding OK /
  descriptor_bindings OK / designated_source_context OK / gating_snapshot OK /
  gating_spec OK / holdout_bindings OK / holdouts OK / initial_role_metrics OK /
  leakproof_context OK / role_contracts OK / role_files OK /
  role_payload_allowlist OK / stop_policy OK / workloads OK
  whiteboard NG  authority value 'whiteboard' must not be an empty array
```

- **`leakproof_context` を `{"text": LEAKPROOF_CONTEXT}` で包むと通る。** (P1-a) の裏取り。
- **`whiteboard` の空配列だけが唯一の不合格 key である。** (P1-b) が本 wave の唯一の設計択一。
- `_INITIAL_ROLE_METRICS` は 5 key すべて値が `null` だが、非退化検査も canonical JSON も通る。
- **限界:** `baseline` / `descriptor_binding` / `gating_snapshot` / `descriptor_bindings` の 4 key は
  実 resolver の出力でなく健全な代用 mapping で測った。型・非退化の観点では通るが、
  実値でも通るかは段 6 で実装子の実装を通して確かめる。
- 先行 wave (T-1380) が挙げた 3 矛盾のうち、`leakproof_context` は射影で解け、
  `descriptor_binding` は型としては解ける。**残るのは whiteboard 1 件だけである。**

## M13. plan が挙げた 18 key の出所はすべて実在し非退化

`FORMAL_WORKLOADS` は import 時に `s8b_holdout_freeze.HOLDOUTS` から構築され、
`rr80` / `rr20` の 2 件を持つ (定義行の `= {}` は初期化であって空ではない)。
`ROLE_FILES` 4、`ROLE_CONTRACTS` 4、`ROLE_PAYLOAD_KEY_SPEC` 6、`GATING_SPEC` 351 字、
`DESIGNATED_SOURCE_CONTEXT` 868 字、`TR.HOLDOUT_BINDINGS` 2 件、`snapshot_gating_spec` と
`resolve_arm_input` も実在する。`TrialBinding` は `prereg_content_commit` を持つ。

## M14. plan が変える既存 fixture (段 4 で裁定が要る)

`test_s8c_schedule.py:69` と `test_s8c_preregistration_predicates.py:101` の
`"whiteboard": [{"status": "initial"}]` を plan は exact `[]` へ変える。
**これは既存テストの入力値の変更であり、DW-S05-B の「既存テストの期待値を変えない」に接する。**
弱める向きか強める向きかを段 4 で裁定する。plan の主張は「非空を拒否し空だけを受理するので
受理集合は単調に広がらない」である。
