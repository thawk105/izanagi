実装済み・未実走です。pytest は実行していません。commit と docs 編集もしていません。

変更した file:

- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json`
- `orchestrator/campaign/s8c_preregistration_evidence.py`
- `orchestrator/campaign/s8c_preregistration.py`
- `orchestrator/tests/test_s8c_preregistration_predicates.py`

C05 の registry／契約対応、DECIDER_VERSION v5、負対照 fixture、期待値を更新しました。静的 AST／JSON parse と `git diff --check` は成功しています。

赤になる見込みの既存テストはありません。snapshot の C05 は artifact 未存在のため従来どおり `schedule-schema-absent`、legacy test は動的 registry 導出のため変更不要です。

mutation は `run_trial` の `consume_schedule(...)` 1箇所を `return artifact` に置換します。これにより `_evaluate_c05` の `required_targets <= graph.calls` 到達性検査で `consume_schedule`／`verify_schedule` が不足し、`UNSATISFIED` / `schedule-consumer-unreachable` になります。

## 総括

scope 内の4項目のみを反映し、C05 を machine-checkable 集合へ追加しました。§5、schedule artifact、docs、commit は親の担当範囲として未変更です。