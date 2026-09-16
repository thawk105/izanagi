## 読んだ資料

指定の5資料を読みました。

- `stage4-adjudication.md`
- `stage6-reviewA.md`
- `stage6-reviewB.md`
- `stage5-author.md`
- `D922-verbatim.md`

## F1 の修正 (file:line)

`tools/check_branch_landed.py:1414`

fragment解析成功後、registryが`error`の場合だけ証拠層の理由をregistryの理由へ戻しました。decision計算は変更せず、正常なreceipt不在・blob上限・fragment解析失敗の理由も維持しています。

## F2 の修正 (file:line)

`orchestrator/tests/test_check_branch_rescue.py:1744,1768`

両テストに注入関数の呼出し回数・入力・出力の具体値・説明の変更確認を追加しました。既存の判定値、rc、`decision_inputs`の不変比較も維持しています。

## F5 の修正 (file:line)

`tools/check_branch_rescue.py:1535`

各層に`decisive`を追加。`exact-tree-state`は`not-applicable`以外なら非decisiveでも運びます。判定処理、100件上限、`truncated`の処理は変更していません。

## 更新した本 wave の新規テスト (どこを厳しくしたか)

- `test_real_checker_unlanded_spool_details`：完全一致へexact層・decisive・候補件数を追加し、実Gitで候補0件／2件不一致を検査。
- `test_unproven_details_are_bounded_and_count_all_reasons`：証拠層を`decisive: true`込みの具体的な完全一致へ更新。
- `test_unit_details_do_not_change_assessment_decisions`：注入が1回実行され、具体的な説明が返ることを必須化。
- `test_unit_details_do_not_change_rescue_rc_or_decision_inputs`：注入の実行と具体値がrescue JSONへ届くことを必須化。

## 追加・改訂したテスト (nodeid)

接頭辞は`orchestrator/tests/test_check_branch_rescue.py::`です。

- `test_real_checker_unlanded_spool_details[0]`
- `test_real_checker_unlanded_spool_details[2]`
- `test_unproven_details_are_bounded_and_count_all_reasons`
- `test_unit_details_do_not_change_assessment_decisions`
- `test_unit_details_do_not_change_rescue_rc_or_decision_inputs`

F1の`test_check_branch_landed.py::test_spool_exact_does_not_hide_integrity_errors`は期待値を変更していません。

## 実走結果 (実走した nodeid と範囲、実走できなければその旨)

**実装済み・未実走。実走したnodeidはありません。**

`tools/run_tests.py`で対象2ファイル全体を試行しましたが、`qstat -Q preflight rc=1`でrunnerがrc=16となりました。`child_started=false`でpytest未起動です。

静的確認は成功しました。

- 指定4ファイルの構文解析。
- `git diff --check`。
- `61e0e9c4a`とのAST比較：既存関数66＋70件の変更・欠落なし。

runnerは`output/pegasus-dispatch/375be65041e579573b6e2b1828291897/receipt.json`を自動生成しました。

## 所有外への波及可能性 (静的列挙)

- cleanup・台帳記帳consumer：証拠層の追加fieldと正しいregistry理由を受け取ります。
- `conftest.py`・収集設定・所要台帳：parametrize追加により収集nodeが1件増えます。
- `test_plain_runner_coverage.py`、`test_pytest_collection_config.py`、`test_acceptance_schedule_order.py`：収集数・被覆率への影響は未実走です。
- `test_branch_rescue_ledger.py`・`test_check_docs.py`：関連consumerとして確認余地があります。

## 直さなかったもの と その理由

指示どおり、変異登録の再照準、上限超過時の正例優先、`report_sha256`の記録訂正、mergeテストのbatch到達確認には触れていません。

docs編集、commit、stage、push、remote操作はしていません。

## 総括

F1・F2・F5を指定範囲内の3ファイルに実装しました。wave開始前の既存テストは不変です。**pytest未起動のため、closedとは申告しません。**