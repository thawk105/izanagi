## 総括

D438 と brief に実装上の食い違いはありません。受理集合は不変で、`SATISFIABLE_CONDITION_IDS == frozenset()`、新規 `SATISFIED` 経路はありません。commit、`git add`、docs 編集は行っていません。

変更 path:

- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json`
  - C01/C04/C09/C10/C11/C12 のみ `machine_checkable: true`
  - C11 を廃止済み sample-plan/cap-lift から generation projection へ差し替え
  - C03/C08 を content/effective commit の二段束縛へ改訂
- `orchestrator/campaign/s8c_preregistration_evidence.py`
  - C11 の射影 blob・5 識別子検査を追加
  - 不要になった `_artifact_object` を削除
  - `_MACHINE_EVALUATORS` 由来の `MACHINE_CHECKABLE_CONDITION_IDS` を追加
  - `cap < 2` と全評価器の未定義終端を維持
- `orchestrator/tests/test_s8c_preregistration_core.py`
  - path inventory を39件へ更新
  - live contract hash を実測値へ更新。g1 歴史値は不変
- `orchestrator/tests/test_s8c_preregistration_predicates.py`
  - status snapshot、6負例、C11 fixtureを追随
  - C02評価器不在、旧契約互換、C11射影正負対、C03/C08自己参照禁止、契約・評価器双方向整合の境界テストを追加
- `test_s8c_preregistration_invariant.py` は読了しましたが変更不要でした。

実測値:

- contract hash: `a33e04a763f3cd41909a3c376878b0bce1449e59a8ad29462138a6302ffbf4ae`
- path inventory: 39件
- 6条件の現HEAD status vector:
  - C01 `UNSATISFIED/workload-projection-mismatch`
  - C04 `UNSATISFIED/crash-policy-cell-partial`
  - C09 `UNSATISFIED/formal-acceptance-layer3-consumer-absent`
  - C10 `UNSATISFIED/cross-binding-verifier-incomplete`
  - C11 `EVIDENCE_UNDEFINED/completion-proof-not-machine-checkable`
  - C12 `UNSATISFIED/environment-contract-consumer-absent`

直接評価 probe は rc=0 で、全6件の baseline は未定義終端、mutation は個別 `UNSATISFIED` でした。C02評価器不在は `ERROR/commit-blob-read-error`、C11射影欠落・識別子破壊は `UNSATISFIED/critic-feedback-consumer-absent` でした。strict loader、4 Python fileのAST parse、`git diff --check` も成功しています。

pytest は指定3ファイル全域を `tools/run_tests.py` 経由で投入しましたが、予約台帳へのsandbox書込み不可と `qstat -Q` preflight失敗により、pytest起動前に rc=16 で停止しました。実走 nodeid は0件です。したがって緑とは申告しません。期待赤 `test_candidate_freeze_matches_contract_and_generation_chain` も未観測で、回帰赤の有無もpytestでは未確定です。

波及候補は `s8c_preregistration.py` の activation/freeze chain、親所有のg3凍結記録と規範docs、将来の `trial_registry.py` 二段束縛consumer、exact `G=2` 受入consumer、共有 `NEGATIVE_CONTROL_CASES` fixture、holdout scan invariantです。作業ツリーには親所有と思われる2 docsの並行差分がありますが、触れていません。

親への残作業は、外側環境で指定pytestを再走し、docs確定後にg3を生成することです。二段束縛consumer、exact `G=2` consumer、評価器bytesの凍結範囲はそれぞれT-1187、T-1185、T-1186のままです。