## 所見対応表

| 所見 | 状態 | 結果 |
|---|---|---|
| R1 | partial | bootstrap の loop 変数を変更済み。既存テストは無変更。dispatch 失敗により未実走 |
| R9 | partial | floor の drift 主張を撤回し、現 HEAD == receipt commit を fixture で検査。gate は無変更。未実走 |
| R7 wrapper 正例 | partial | 実 admission fixture が未統合のため **A' 待ち**。stub を実 fixture へ勝手に置換せず停止 |

`regressed` はありません。未実走のため `closed` とは報告しません。

## 変更内容

- [floor_campaign.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix-b/tools/pegasus/floor_campaign.sh:39)
  - bootstrap loop を `preflight_py_name` に変更。
  - 後段の既存文字列 `for py_name in python3 python3.10...` を最初に拾えるよう修正。

- [test_pegasus_floor_tools.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix-b/orchestrator/tests/test_pegasus_floor_tools.py:253)
  - floor fixture の A→B drift commit を削除。
  - 現 HEAD と receipt に記録する source commit の一致を明示検査。
  - 既存テストの期待値・assert の反転、緩和、skip、削除はなし。

`t126_qualification.sh` と `test_t126_pegasus_tools.py` は変更していません。

## 検査結果

次の nodeid を `tools/run_tests.py` 経由で指定しました。

- `test_floor_job_records_interpreter_resolution_failure_after_attempt_creation`
- `test_floor_wrapper_preflight_rejection_is_nonmutating_and_starts_no_driver`
- `test_floor_wrapper_accepting_source_commit_preflight_reaches_first_write`

結果は runner rc=16 でした。submodule marker 未初期化の警告後、計算ノード dispatch の `qstat -Q` preflight が rc=1 で失敗し、pytest は実走していません。直接 pytest への切り替えは行っていません。

静的検査結果:

- `bash -n tools/pegasus/floor_campaign.sh`: 成功
- `git diff --check`: 成功
- 変更範囲: 所有対象2ファイルのみ
- commit / add / push: 未実施

新規 wrapper 結合テストは追加していません。R9 の修正により、既存 floor 正負2 fixture の `git init` は計2回のまま、commit 数は計6回から計4回へ減ります。受入全走時間を押し上げる変更ではありません。

## 最初の書込み前に保護した範囲

実装構造について言えるのは次の限定です。

> PBS が job body を開始した後、当該 wrapper が明示的に管理する durable output および scratch を初めて変更する前に、submission / source identity・current registry・protocol / control・calibration bytes・compute-site の静的 read-only admission を完了する。

ただし実 domain admission を通る wrapper 正例は A' 待ちで未実装、かつ対象テストも未実走です。そのため、この保証を実走済みとは報告できません。

対象外なのは qsub 側の receipt / ledger、PBS spool / prologue / epilogue、scheduler が作る `$TMPDIR`、filesystem atime、full hardware attestation probe の scratch です。また floor の現 HEAD 一致 gate は最初の書込み後に動くため、A→B drift 耐性や「write-zero」は主張できません。

## 直せなかった項目

R7 wrapper 正例は **A' 待ち**です。現 snapshot にある正例は環境変数駆動の自己完結 stub、Python CLI 正例は mocked `admit()` のままで、A' が作る current registry・protocol/calibration・receipt/ledger/qsub binding の実 fixture は参照できませんでした。

## 総括

R1 と R9 は実装済み・未実走です。R7 は A' fixture 未統合のため partial のまま停止しました。作業ツリーには所有範囲内の2ファイルだけが変更されています。