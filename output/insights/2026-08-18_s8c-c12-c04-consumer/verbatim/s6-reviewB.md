## 所見

[RB-1] `restart_forbidden` は実行時に読まれず、`started_once` も拒否判定には使われていない。  
(a) 主張: `forbid_trial_restart` は状態を書くだけで、実際の拒否は別の durable start row 判定に依存する。  
(b) 根拠: `trial_registry.py:217-228`, `:1928-1937`, `:1958-1965`; `p3_autonomous_workload_trial.py:3437-3451`。  
(c) 成果物影響: C04 が列挙する flag 自体を壊しても再起動拒否の挙動が変わらず、恒真な証拠面になる。  
(d) 最小の是正: flag を読む拒否 consumer を追加するか、flag を契約から外し durable row consumer を正本として明記する。  
(e) 自信度: 高。

[RB-2] C04 の契約 edge は実装されているが、判定器がその edge を検査していない。  
(a) 主張: `run_trial preflight -> reject_started_trial` は `p3_autonomous_workload_trial.py:3674-3679` にある。しかし判定器は `mark_experiment_indeterminate` と `forbid_trial_restart` しか要求しない。  
(b) 根拠: 契約 JSON `:163-177`; `s8c_preregistration_evidence.py:1611-1621`。機械集合は再導出済みで、CHECKS 43 件、EXCLUSIONS 30 件、差分なし。  
(c) 成果物影響: `reject_started_trial` を削除しても C04 の判定結果が変わらず、契約違反を受入で検出できない。  
(d) 最小の是正: 次の判定器変更枠で C04 の declared call target に `reject_started_trial` を追加し、削除変異を検査する。  
(e) 自信度: 高。

[RB-3] `do_build=False` の site 推定が transport opt-in を実 site と誤認する。  
(a) 主張: `p3_autonomous_workload_trial.py:2167-2168` は no-build で site を返さず、`:3663-3668` が flag だけで `OTHER`/`PEGASUS_COMPUTE` を選ぶ。  
(b) 根拠: `p3_s4_loop_trigger_gating.py:95-98`, `env_contract.py:256-260,292-301`; origin 経路は `p3_autonomous_workload_trial.py:1253-1254,3923-3963`、CLI は `:4041-4044,4089-4111`。  
(c) 成果物影響: OTHER の no-build + opt-in は不要な予約拒否となり、実 Pegasus compute の no-build + opt-out は予約検査を迂回する。origin は戻り値が変わり、CLI は `ReservationError` で停止し得る。  
(d) 最小の是正: 実際の `trigger._current_site()` を一度だけ解決し、build・origin・reservation へ同じ値を渡す。flag から site を推定しない。  
(e) 自信度: 高。

[RB-4] 並行 wave の stale patch は status snapshot、exact pin、lifecycle schema の三面で衝突する。  
(a) 主張: t1348 は C04 を未実装扱いする pin/snapshot を残し、t1353 は lifecycle v1 を v2 に変更して `record_trial_start_once` に `attempt_slot` を要求する。  
(b) 根拠: 本差分 `test_s8c_preregistration_invariant.py:43-127`, `test_s8c_preregistration_predicates.py:139-183`, `trial_registry.py:51-94`, `p3_autonomous_workload_trial.py:3680-3693`; t1348 の同名 files `:43-123,139-183`; t1353 `trial_registry.py:3693-3704`。  
(c) 成果物影響: 先に land する順序により exact 集合検査、C04/C12 snapshot、または lifecycle start 呼出しが機械的に赤くなる。  
(d) 最小の是正: 両 wave を rebase し、C04/C09/C10 の pin と現行 status を union で再導出し、lifecycle v1 と t1353 の API 変更を手動裁定する。  
(e) 自信度: 高。

## 受入で赤くなる可能性のある検査の一覧

焦点走の 10 file 外で、未実行の受入面。

- `orchestrator/tests/test_reflux_originless_compatibility.py:116-132` — `run_origin_trial` 経路。
- `orchestrator/tests/test_campaign.py:9184` — CLI `main` 経路。
- `orchestrator/tests/test_s8b_repo_scan_invariant.py:27` — repo scan invariant。
- `orchestrator/tests/test_campaign_import_invariant.py:1078,1218-1232` — campaign source scan/import invariant。
- `orchestrator/tests/test_real_repo_serialization.py:767-780` — real-repo fixture closure。
- `orchestrator/tests/test_pytest_failure_digest.py:780` — real `conftest.py` 受入。
- `orchestrator/tests/test_p3_build_authority_cli.py:619` — production AST closure。
- `orchestrator/tests/test_reflux_formal_consumer.py:824` — production file set/source scan。
- `orchestrator/tests/test_check_ai_provenance.py:1507` — commit provenance。
- `orchestrator/tests/test_check_docs.py:1`, `tools/check_docs.py:12`, `tools/check_ai_provenance.py:1` — checker entrypoints。禁止指定行付近は読んでいない。

fixture は `conftest.py:95` の function-scope で、重複名や共有 fixture 数の pin は検索上見つからない。pytest は実行していない。

## 総括

受入可とは判定しない。最重要は no-build の site 誤推定と、restart flag の未接続である。  
C04 の named edge は実装済みだが、判定器は未検査のままである。  
機械 pin の再導出結果は一致している。  
A-1、A-5、A-6、A-7、および判定器本体の scope 逸脱は差分上確認できない。  
焦点走と親報告以外の全走は未確認であり、緑とは報告しない。