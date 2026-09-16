## 現状の読取り (1 巡目差分の確認)

1巡目の差分を読み、実装を引き継いで残作業を完了しました。今回の追加編集はテスト2ファイルのみです。

- branch: `impl-dev-wave-t2590-a1-sized-source-contract`
- HEAD: `d6f12ed7d`
- 最終差分: 所有6 pathのみ。tracked 5ファイルは520行追加・42行削除、v2 JSONは新規のまま。
- commit・docs編集・本走投入はしていません。

凍結対象のSHA-256は開始時の値を維持しています。

| 対象 | SHA-256 |
|---|---|
| v2 JSON | `b50a4edf86250033aa0e2b18efa2d7842d7c90025fdb901011fdad7adf052fe1` |
| sized追補README | `6093de244e6fc90607094608617032f427db4951ebffc847c7bcaa795309789b` |

## test 8 の訂正

公開pilot receiptの`source_binding`を、そのまま次の2関数へ渡す形に訂正しました。両方Trueです。

- `_validate_source_binding(binding, pilot_policy)`
- `binding_matches(binding["files"])`（既定pilot）

歴史module SHAの書換え、validatorの受理条件変更はありません。

## sized measurement 経路 test と pilot attempt 拒否 test

measurement fixtureにpolicy・事前登録・契約/module/patch/追補・`sizing_inputs`の2ファイルを実bytesで配置しました。policy load、契約検算、intent再構成とsource照合、hydrateのenv・staged root照合は実関数を通しています。

materializer・依存準備・condition gate・campaignはstubです。scheduler/runtime admissionと永続化周辺も軽量化しています。

確認した内容は次のとおりです。

- sizedの`attempt-0002`でmeasurementが完了する。
- materializerが受けた`study_id`はsizedである。
- 依存準備・condition gate・campaignへ同じcontext rootが渡る。
- env不一致・scratch不一致はmaterializer到達前に指定文言で拒否される。
- pilotの`attempt-0001`はmeasureでも`A1 source amendment requires pilot attempt-0004`で拒否される。

pilot submit拒否テストには、誤って到達しても実際に投入しないqsub stubを追加しました。

## 新規 test の nodeid と直接呼出し / pytest 結果

略記は以下です。N番号は次節のnodeid参照にも使います。

- TJ = `orchestrator/tests/test_paper_story_a1_job_contract.py`
- TP = `orchestrator/tests/test_paper_story_a1_paired.py`

**全14 nodeで`DIRECT_CALL_PASS`、復元後のpytestでもPASSです。**

| ID | nodeid |
|---|---|
| N1 | TJ::test_sized_source_closures_match_job_and_driver |
| N2 | TJ::test_sized_submit_requires_hydrate_and_preserves_attempt_names |
| N3 | TJ::test_sized_group_intent_requires_hydrate |
| N4 | TJ::test_sized_job_stages_hydrate_for_measurement |
| N5 | TJ::test_sized_ccbench_acceptance_rejects_dirty_source |
| N6 | TJ::test_sized_source_context_reaches_trace_and_perf_validation |
| N7 | TJ::test_sized_measurement_routes_amended_source_and_hydrate |
| N8 | TJ::test_pilot_measurement_attempt_pin_remains_enforced |
| N9 | TJ::test_pilot_attempt_pin_remains_enforced |
| N10 | TP::test_sized_source_contract_pins_bytes_and_four_bindings |
| N11 | TP::test_sized_amendment_binding_rejects_single_changed_input |
| N12 | TP::test_pilot_published_source_binding_remains_accepted |
| N13 | TP::test_sized_consumer_accepts_amended_configure |
| N14 | TP::test_sized_consumer_rejects_admission_mismatch |

pytestは実走できました。

| 実行 | 結果 |
|---|---|
| 指定された2ファイル・`-k`式 | **129 passed, 338 deselected / 61.95秒** |
| 変異復元後、新規テスト＋pilot measure＋既存v3 submit・measurement AST・境界配線 | **101 passed, 366 deselected / 21.46秒** |

両実行には重複があります。指定の`-k`式では選択されないN8も、後者で実走しています。

## 反実仮想 (検査除去で赤化) の結果

実装ファイルを一時編集して個別プロセスで直接呼出しし、各回`finally`で元のbytesへ復元しました。

| nodeid参照 | 除去・変更した対象 | 観測 |
|---|---|---|
| N1 | sized契約登録／driver閉包追加／shell terminal追加（M1/M4/M5） | 各`AssertionError`、KILLED |
| N2 | submitのhydrate存在検査 | 後段の拒否文言とのregex不一致、KILLED |
| N3 | sizedのhydrate必須（M9） | `DID NOT RAISE PaperStoryError` |
| N4 | sizedのshell staging（M6） | 引数照合の`AssertionError` |
| N5 | tracked dirty拒否 | `DID NOT RAISE PaperStoryError` |
| N6 | `validate`内のmaterialization検査呼出し | 呼出し記録の`AssertionError` |
| N7 | study非依存attempt固定（M8） | sized正例がpilot用エラーで失敗 |
| N7 | env照合／scratch照合 | 各`DID NOT RAISE PaperStoryError` |
| N7 | materializerへのstudy引渡し | 受領引数の`AssertionError` |
| N8 | pilot measureのattempt検査 | `DID NOT RAISE PaperStoryError` |
| N9 | pilot submitのattempt検査 | qsub stubへの到達で`AssertionError` |
| N10 | 契約bytes検算／amendment検算（M2/M3） | 各`DID NOT RAISE RuntimeError` |
| N11 | sized binding照合（M10） | 改変binding受理で`AssertionError` |
| N12 | pilotの契約閉包追加 | 公開binding検証の`AssertionError` |
| N13 | amended admissionの発火をv1限定化（M7） | `trace0-source-route-incomplete`で正例失敗 |
| N14 | admissionの`tracked_clean`検査 | 不正証拠受理で`AssertionError` |

**負例20変異はすべてKILLED。** 等価コメント追加のM0はSURVIVEDです。

復元時のbytes一致、復元後の`git diff --stat`・`git diff --check`を確認しました。変異は残っていません。

## 既存 test への波及と関数名集合

`rg -c '^def test_'`とASTによる関数名集合比較の結果です。

| ファイル | HEAD | 最終 | 消失 |
|---|---:|---:|---|
| TJ | 88 | 97 | なし |
| TP | 133 | 138 | なし |

既存test本体の変更は、measurement ASTテストへのstudy引渡しassert追加1件のみです。既存assertの削除はありません。共有submit fixtureの既存callerも追加のpytestで確認しました。

`_trace0_commands_match`、`SourceContext.validate`、`prepare_dependencies`、`configure_dependencies`はHEADとのAST一致を確認しています。pilot限定のsizing出力分岐も変更していません。

## 所有外 caller の表

指定された6検索式で`orchestrator/`と`tools/`を横断検索しました。

| caller・参照箇所 | 判定 |
|---|---|
| `pipeline.py:1097` | `SourceContext`の型確認と`validate`。契約選択済みcontextを受けるため変更不要 |
| `manual_probes/test_t2397_a1_source.py:66–75` | pilot専用。`materialized`・`load_contract`の既定pilotを維持 |
| `tests/test_campaign.py:13959` | 不正context型の拒否テスト。study選択不要 |
| TJ既存materializer呼出し | pilotの既定値を維持 |
| TP既存amendment bindingテスト | `load_contract`の既定pilotを維持 |
| 共有`_v3_submit_cli_fixture` | 既存callerはpilot/attempt-0004、新規sized callerは明示引数 |
| driverの契約load・binding・materializer | study引渡しが必要な箇所は所有path内で対応済み |
| source module内部 | load・context生成まで同じstudyを引渡し済み |
| job script | 所有path内の3閉包とstagingで二値選択済み |
| `s8c_result_judge`、backoff系、sort oracle、layer3、T-2000 probeの検索一致 | 別関数名への部分一致。A1 source APIのcallerではない |

**所有外に、追加でsizedを渡す必要のあるcallerは見つかりませんでした。**

## 未実装・未実走・判断を要する点

本段の残作業に未実装・裁定待ちはありません。

- 全テストスイート、実materialization・build・性能測定は未実走です。今回の結果は軽量fixtureと選択したpytestの範囲です。
- 親による正式な変異較正・受入は本段の反実仮想とは別です。
- 補助的な`bash -n`はPreToolUse hookに拒否され未実行です。shellの指定区間はテストで実評価しています。

受理集合について、変更前はpilot attempt-0004限定、sized measureは全拒否でした。変更後はsizedのamended契約とhydrateを必須とし、attempt名を固定しません。契約なしsizedの旧5/10 path bindingは拒否され、v2入り9/14 pathが対象になります。

## 総括

1巡目の実装を維持して残作業を完了しました。新規14テストは直接呼出し・pytestとも通過し、負例20変異を検出、全変異を復元済みです。凍結bytesと所有6 pathの境界を守った未commit差分を残しています。