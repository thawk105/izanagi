## 変更 file と差分の要約

**test 8 の指定期待値が変更前から成立しないため、指示に従い停止しました。実装は未完了です。**

所有する 6 path のみに差分があります。

- `paper_story_a1_source.py`: 固定 2 study の契約表と study 引数。
- `paper_story_a1_source.v2.json`: 新規作成。
- `paper_story_a1_paired.py`: 指定された分岐を置換。
- `paper_story_a1_paired.sh`: 3 閉包と hydrate staging を対応。
- test 2 file: fixture 拡張、新規 12 test、AST assert 追加。

commit・本走投入・docs 編集はしていません。

## 契約表と v2 JSON (digest 込み)

pilot 定数と既定引数を維持し、sized 契約を追加しました。v2 は指定の 11 key、`attempt` なしです。

SHA-256:

- v2 JSON: `b50a4edf86250033aa0e2b18efa2d7842d7c90025fdb901011fdad7adf052fe1`
- 追補 README: `6093de244e6fc90607094608617032f427db4951ebffc847c7bcaa795309789b`

追補は親の検算値と一致。v2 作成後の bytes は変更していません。

## driver の分岐置換 (アンカー別)

| 変更前アンカー | 適用した変更 |
|---|---|
| D:2243 | 契約表から source paths を追加 |
| D:2636 | sized 全 attempt に契約検算・hydrate 必須 |
| D:3409 | 両 study の契約・hydrate 検査、attempt 制限は pilot のみ |
| D:4860 | 閉包内の契約 path から binding の study を選択 |
| D:5219 | 両契約で amended admission 検査を発火 |
| D:7126 | study 別 load、study 不一致と pilot attempt 不一致を分離 |
| D:7137 | materializer へ `study_id` を渡す |

`_trace0_commands_match` と pilot 限定の sizing 出力は変更していません。

変更前は pilot attempt-0004 限定、sized は D:7127 で全拒否でした。

## job script の分岐置換

3 箇所で契約・追補 path を二値選択し、共通 module・patch は各箇所 1 出現を維持しました。

直接呼出しで、pilot/sized 双方の順序込み 14/9 path、文字列出現数、sized staging のコピーと引数を確認しました。

## 新規 test の nodeid と直接呼出し結果

略記:

- TJ = `orchestrator/tests/test_paper_story_a1_job_contract.py`
- TP = `orchestrator/tests/test_paper_story_a1_paired.py`

| nodeid | 結果 |
|---|---|
| TJ::test_sized_source_closures_match_job_and_driver | DIRECT_CALL_PASS |
| TJ::test_sized_submit_requires_hydrate_and_preserves_attempt_names | DIRECT_CALL_PASS |
| TJ::test_sized_group_intent_requires_hydrate | DIRECT_CALL_PASS |
| TJ::test_sized_job_stages_hydrate_for_measurement | DIRECT_CALL_PASS |
| TJ::test_sized_ccbench_acceptance_rejects_dirty_source | DIRECT_CALL_PASS |
| TJ::test_sized_source_context_reaches_trace_and_perf_validation | DIRECT_CALL_PASS |
| TJ::test_pilot_attempt_pin_remains_enforced | DIRECT_CALL_PASS（submit のみ） |
| TP::test_sized_source_contract_pins_bytes_and_four_bindings | DIRECT_CALL_PASS |
| TP::test_sized_amendment_binding_rejects_single_changed_input | DIRECT_CALL_PASS |
| TP::test_pilot_published_source_binding_remains_accepted | **DIRECT_CALL_FAIL: AssertionError** |
| TP::test_sized_consumer_accepts_amended_configure | DIRECT_CALL_PASS |
| TP::test_sized_consumer_rejects_admission_mismatch | DIRECT_CALL_PASS |

pytest runner は未実走です。

## 反実仮想 (検査除去で赤化) の結果

**未実施です。** test 8 の仕様不整合を確認して停止しました。検査除去の変異は作業ツリーに残っていません。

## 既存 test への波及と関数名集合

| file | 前 | 後 | 消失した関数名 |
|---|---:|---:|---|
| TJ | 88 | 95 | なし |
| TP | 133 | 138 | なし |

既存 assert・期待値・関数名は維持しました。submit fixture に既定値付き引数を追加し、既存 AST test に study 引渡し assert を追加しています。

既存 test 全体の回帰は未実走。`git diff --check` は通過しました。

## 所有外 caller・共有 fixture・consumer test への波及 (静的列挙)

- `pipeline.py:1097`: 同じ `SourceContext` 型を参照。変更不要。
- `orchestrator/manual_probes/test_t2397_a1_source.py`: 既定 pilot の `materialized` / `load_contract` 呼出しを維持。
- `_v3_submit_cli_fixture`: 既存 caller は既定 pilot/attempt-0004、新規 sized caller は明示引数。
- consumer 新規 test は既存 `_arm` とバイナリ fixture を利用。
- 所有外 caller の網羅的監査は未完了です。

## 未実装・未実走・判断を要する点

停止理由は、公開 `receipt.json["source_binding"]` が **terminal 用 9 path** である一方、指定の `_validate_non_certifying_source_binding` が **14 path** を要求することです。

変更前 HEAD の対象関数を抽出して評価しても、結果は同じでした。

| 公開 binding の検証 | 変更前 | 変更後 |
|---|---|---|
| `_validate_source_binding` | True | True |
| `_validate_non_certifying_source_binding` | False | False |
| `binding_matches` | 未再実測 | True |

歴史 module SHA の書換え、期待値変更、受理条件の緩和はしていません。**test 8 の呼出先を terminal 用 validator に訂正するか、親の判断が必要です。**

残作業:

- sized measurement fixture と経路 test。
- pilot measure の attempt 拒否 test。
- 新規 test ごとの反実仮想。
- pytest・既存回帰検査。

## 総括

指定分岐の実装と新規 11 test の直接呼出しは通りましたが、**完了・受入可能とは報告できません**。指定 test 8 の変更前からの不成立を確認し、赤い test を含む所有 6 path の差分を残して停止しています。