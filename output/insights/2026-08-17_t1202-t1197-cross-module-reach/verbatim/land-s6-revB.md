## 所見

### B-1. golden fixture 作成が campaign 全体の規模に比例し、5 回重複する

- 分類: real
- 深刻度: should-fix
- 根拠: `orchestrator/tests/test_s8c_preregistration_predicates.py:70-100` は、到達可能性と無関係に追跡中の `orchestrator/campaign/*.py` をすべて列挙、archive、展開する。この処理は同ファイルの `:113`, `:122`, `:135`, `:159`, `:170` から別々に呼ばれる。現在でも 139 Python file、約 4.5 MB を各回複製するため、campaign module が増えるほど焦点走が線形に遅くなる。
- 失敗シナリオ: consumer や wave の追加で campaign が育つたび、到達対象外の module まで5回複製され、過去に是正した AST 走査共有とは別経路で受入時間が再び膨張する。
- 成果物影響: certified 選択、ActivationReport、台帳値は変わらないが、焦点走と受入全走の時間予算を圧迫し、必要な検査を完走できない可能性を増やす。

### B-2. 親の「実 tree では C01 も cross-module 走査を実行する」という根拠が成立していない

- 分類: real
- 深刻度: should-fix
- 根拠: `orchestrator/campaign/s8c_preregistration_evidence.py:1384-1385` で C01 は `workload-projection-mismatch` を返し、直後の graph 取得 `:1386` に到達しない。golden も `orchestrator/tests/test_s8c_preregistration_predicates.py:140` でこの早期終了を固定している。したがって実 tree で共有走査を実行するのは C04 と C09 であり、C01 ではない。
- 失敗シナリオ: 段 6 の記録を根拠に「C01 の実 tree cross-module 経路も検査済み」と判断すると、C01 の reachability regression が専用 fixture 以外で露出しない事実を見落とす。
- 成果物影響: 現在の certified 選択と ActivationReport 値は変わらないが、台帳に残る検証範囲の説明が実際より広くなり、C01 consumer 到達の保証を誤って参照させる。

### B-3. 削除済み C12 attribute gate 専用 helper が無参照で残っている

- 分類: real
- 深刻度: backlog
- 根拠: `orchestrator/campaign/s8c_preregistration_evidence.py:311` の `_attributes` は、旧 `{"single_process", "allow_resume"}` 判定の削除後、production と test のいずれからも参照されていない。静的な定義・参照突合では、この evaluator 内で唯一の無参照 private top-level helper だった。
- 失敗シナリオ: 後続変更が旧 gate の現役 helper と誤認し、撤回済みの attribute 判定を再導入する足場になる。
- 成果物影響: 現状では certified 選択、ActivationReport、台帳、受理集合の値を変えない。

## B1 合成意図の突合

`181b7350 -> main` と `181b7350 -> d61aab21` を別々に確認し、最終 tree と項目単位で突合した。

- T-1167 の allocation 縮小は残っている。`_c12_allocation_binding_verdict` は `orchestrator/campaign/s8c_preregistration_evidence.py:1550-1565` に存在し、`read_binding` と `check_reservation` を同一関数内で要求する。
- C12 は allocation-first のまま。`orchestrator/campaign/s8c_preregistration_evidence.py:1572-1576` が allocation gate、`:1577-1601` が後続の cross-module environment/guard 判定である。
- main が追加した二つの C12 防壁は維持されている。
  - `orchestrator/tests/test_s8c_preregistration_core.py:497-516`
  - `orchestrator/tests/test_s8c_preregistration_core.py:519-534`
- branch の cross-module 化は C01、C04、C09、および C12 の allocation 後に残っている。
- graph cache は `orchestrator/campaign/s8c_preregistration_evidence.py:1225-1231`, `:1346-1353` に残り、`PredicateRegistry.evaluate_all` の `:1698-1725` で全条件に共有される。
- 両親側に存在した test function 名の欠落はなく、main が意図的に削除した `single_process_required` と旧 attribute gate の production/test 復活もない。
- 未定義名へ至る経路、残存 conflict marker、差分 whitespace error は静的確認では見つからなかった。
- 指定された `66801060` と実際の merge parent `699c9cae` の間に、対象 consumer 群の追加差分はない。

## B3 所有外 consumer の判定

| consumer | 判定 | 根拠 |
|---|---|---|
| `test_s8c_preregistration_invariant.py` | 影響なし | `:165-194` は実 report を読むが、freeze、decider、`effective=False` のみを検査し、predicate 理由や digest literal を固定しない。 |
| `test_reflux_originless_compatibility.py` | 影響なし、更新不要 | `:31-91` の bundle は synthetic report を使用する。golden `:234` は main 側の更新値がそのまま残っている。 |
| `test_reflux_origin_binding.py` | 影響なし | `:101-128` で predicates が空の synthetic ActivationReport を注入する。実 evaluator は呼ばれない。 |
| `test_p3_autonomous_workload_trial.py` | 影響なし | `:5248-5273` が digest `"3"*64` の synthetic report を monkeypatch する。 |
| `s8c_generation_projection.py` と test | 影響なし | production `:1-5` は projection の pure leaf。test の import `test_s8c_generation_projection.py:11` を含め、ActivationReport と digest の参照がない。 |
| acceptance receipt | 影響なし、更新不要 | `s8c_acceptance_receipt.py:252-255`, `:343` は digest を opaque SHA-256 として検証・保存するだけ。test は `test_s8c_acceptance_receipt.py:97-121` の synthetic 値を使う。 |
| completeness | 影響なし、更新不要 | `autonomous_trial_completeness.py:955-986`, `:1041-1055` は report と launch admission の一致と形式を検査する。test は `test_autonomous_trial_completeness.py:508-560` の synthetic 値。 |
| trial lifecycle / registry | 期待値更新不要 | `trial_registry.py:1343-1366`, `:2243-2255`, `:2537-2551`, `:2625-2633`, `:2683-2690` は実行時 digest を伝播・照合する。test fixture は `test_trial_registry.py:1188-1220` の synthetic report で、evaluator digest の literal は固定しない。 |
| layer3 report | 影響なし | `test_layer3_report.py:299` は opaque synthetic digest だけを使う。 |
| core digest test | 影響なし | `test_s8c_preregistration_core.py:2096-2111` は実 report から動的に digest を導出し、固定値を持たない。 |

したがって、親の旧 R7 にある「reflux golden digest が evaluator 変更で変化する」という説明は現在の synthetic 経路には当てはまらない。最終 tree の golden 自体は main 側の値を保持しており、追加更新は不要である。

## B4 実 tree golden

`orchestrator/tests/test_s8c_preregistration_predicates.py:128-152` の全12条件は実装の制御フローと一致する。

| 条件 | status | reason |
|---|---|---|
| C01 | `UNSATISFIED` | `workload-projection-mismatch` |
| C02 | `EVIDENCE_UNDEFINED` | `arm-binding-declared-only` |
| C03 | `EVIDENCE_UNDEFINED` | `manifest-registry-proof-undefined` |
| C04 | `UNSATISFIED` | `crash-policy-cell-partial` |
| C05 | `EVIDENCE_UNDEFINED` | `schedule-schema-absent` |
| C06 | `EVIDENCE_UNDEFINED` | `budget-consumer-contract-undefined` |
| C07 | `EVIDENCE_UNDEFINED` | `floor-judge-contract-undefined` |
| C08 | `EVIDENCE_UNDEFINED` | `prereg-binding-proof-undefined` |
| C09 | `UNSATISFIED` | `formal-acceptance-layer3-consumer-absent` |
| C10 | `UNSATISFIED` | `cross-binding-verifier-incomplete` |
| C11 | `EVIDENCE_UNDEFINED` | `completion-proof-not-machine-checkable` |
| C12 | `UNSATISFIED` | `allocation-enforcement-consumer-absent` |

C12 は allocation gate が先に確定するため単一理由となる。他5条件を含め golden 更新は不要で、親の期待値と一致する。

## B5 走査共有

条件間共有は壊れていない。`orchestrator/tests/test_s8c_preregistration_predicates.py:1668-1718` も、root graph の実解決1回、同一 cache identity、後続 hit を明示的に検査している。

一方、B-1 の snapshot 作成は共有走査とは独立した線形コストであり、今後の repo 成長に伴う回帰点として残る。

pytest は制約どおり実行しておらず、ファイル編集もしていない。判定は差分、参照走査、制御フローの静的検査による。

## 総括

片側の機能意図、C12 の allocation-first、防壁 test、12条件の実 tree golden、所有外 consumer の digest 契約に land を止める欠落は見つからなかった。must-fix はない。B-1 の test fixture コストと B-2 の検証範囲表現は、記録確定後の誤解や継続的な受入時間増加を避けるため是正を推奨する。

GO