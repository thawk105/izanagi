## 読んだ資料

- 指定の `stage4-adjudication.md`
- 指定の `stage6-fix2.md`

## F6 の修正 (file:line)

`orchestrator/tests/test_check_branch_rescue.py:1757,1790`

2本の assert を、子 checker の payload 全体との完全一致へ修正しました。`decision.verdict`、schema、対象 OID を含む全フィールドを具体値で固定しています。

呼出し1回、説明の具体値の出力到達、判定・rc・`decision_inputs` の不変確認は維持しました。

## 実走結果 (実走した nodeid と範囲、実走できなければその旨)

runner で次の2本のみを試行しました。接頭辞は `orchestrator/tests/test_check_branch_rescue.py::` です。

- `test_unit_details_do_not_change_assessment_decisions`
- `test_unit_details_do_not_change_rescue_rc_or_decision_inputs`

`qstat -Q preflight rc=1` により runner は rc=16。`child_started=false` で、**pytest は未実走**です。

静的確認は成功しました。

- 今回の変更は指定2関数のみ。
- `61e0e9c4a` の既存70関数は AST 比較で不変。
- `git diff --check` 成功。

## 直さなかったもの と その理由

指定範囲に従い、実装・他テスト・docs は変更していません。commit・git add・push・remote 操作も行っていません。

runner が dispatch receipt を自動生成しました。

## 総括

F6 の修正は完了しました。実走による緑の確認は、実行基盤の失敗により未完了です。