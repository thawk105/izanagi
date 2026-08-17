## 総括

R3 / R4 の撤回を反映し、C12 を local `main` の allocation-first / module-local 判定へ戻しました。dev-wave 契約に従い、指定外ファイル、stage、merge、commit には触れていません。実装済み・未実走です。

| 項目 | 状態 | 根拠 |
|---|---|---|
| F1 | partial | helper と `_reachable_functions` / `_reachable_calls` は `main` と bytes 一致。全 caller は 2 引数化。pytest 未実走。 |
| F2 | partial | allocation 判定を entrypoint / cross-module 探索より前へ移動。実 tree probe で期待 reason を確認。 |
| F3 | partial | 指定 2 テストの関数ブロックは `main` と bytes 一致。 |
| F4 | partial | `git diff main` の削除 52 行を全件確認。local main の意図を消す残りはゼロ。 |
| F5 | partial | environment 負例 44 fixture と import-form 正例 5 fixture が allocation gate を通ることを静的確認。 |
| F6 | partial | 静的評価可能な `.replace()` 48 式を再検査し、no-op 0。常設 assert は保持。 |

主な変更:

- `_c12_allocation_binding_verdict(workload_supervisor, allocation_consumer)` を完全復元。
- `_evaluate_c12` を allocation → entrypoint → cross-module env/guard の順序へ変更。
- 次の 2 テストを逐語復元。
  - `test_c12_allocation_binding_gate_precedes_environment_gate`
  - `test_c12_allocation_binding_helper_rejects_check_without_read_binding`
- `TOKEN_ONLY_C12` は allocation 呼び出しを main の `read_binding` / `check_reservation` に戻し、env/guard の cross-module 構造は維持。
- R4 固有だった `unbound-check-reservation` を、module-local reachability を検査する `unreachable-check-reservation` へ変更。期待 reason は不変。
- import-form 正例 5 param は env/guard の import 形だけを変異対象とし、allocation 呼び出しを local 名へ統一。

本 wave 側で期待 reason を変更した param はありません。変更したのは fixture 側です。例外として、削除されていた main の gate-order テストを `allocation-enforcement-consumer-absent` 期待へ復元しました。

`git diff main` の残存削除行は、cross-module 探索器・probe cache・C01/C04/C09/C12 env/guard 判定、R5 の動的 mismatch fixture、cross-module 用 fixture への正当な置換だけです。main の allocation helper、順序、期待値を消す行は残っていません。

実 tree の静的 probe 結果:

- C01: `UNSATISFIED / workload-projection-mismatch`
- C04: `UNSATISFIED / crash-policy-cell-partial`
- C09: `UNSATISFIED / formal-acceptance-layer3-consumer-absent`
- C10: `UNSATISFIED / cross-binding-verifier-incomplete`
- C11: `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`
- C12: `UNSATISFIED / allocation-enforcement-consumer-absent`
- C12 の独立 graph probeでは `run_trial`、env `lookup`、guard `attest_and_build_receipt` は到達。ただし通常評価は allocation 第1 gate で停止。

静的な波及先:

- production caller: `_evaluate_c12`、および [s8c_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration.py) の動的 evaluator loader / ActivationReport digest。
- 共有 fixture consumer: import-form、value-flow、dict-carrier、entrypoint cut、test-only、unimported decoy、shadow、local binding、shared-cache、negative-control 各テスト。
- 所有外 consumer:
  - `test_s8c_preregistration_invariant.py`: 実 evaluator を評価するため直接影響。
  - `test_reflux_originless_compatibility.py`: evaluator blob変更により digest golden へ波及し得る。
  - `test_reflux_origin_binding.py`: predicates 空の合成 report のため直接影響なし。
  - `test_p3_autonomous_workload_trial.py`: 合成済み effective report を注入し evaluator を走らせないため直接影響なし。

AST parse 3/3、`git diff --check`、競合マーカー検査、結合文字検査は成功しました。pytest は指示どおり試行していません。3 ファイルは引き続き `UU` のままです。