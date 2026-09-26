## 変更

[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273lc-impl/orchestrator/tests/test_s8b_oracle_driver.py:944) に、flock 下で可視 output の写しを session 中に一度だけ作り、完成後に destination へ複製するメソッドを追加しました。builder は共有 session でこの写しを使い、単独走では従来の直接複製を続けます。新規 test 1 本を追加し、既存の実 builder test に呼出し観測の assert を加えました。commit は作成していません。

## 実走

`PYTHONPATH=. python3 tools/run_tests.py -q -rf -p no:cacheprovider orchestrator/tests/test_s8b_oracle_driver.py -k 'visible_output or output_copy or exact_consumers_and_nodeids'` は **未実走**です。dispatch の `qstat -Q` preflight が rc=1 で失敗し、子テストは起動していません。緑の nodeid はありません。AST 構文解析と `git diff --check` は通過しました。

## 変異の帰属

| 変異 | kill する node | 静的に確認した単一理由・mask |
|---|---|---|
| M1 | `test_t080_shared_base_builds_real_builder_once_across_processes` | 実 builder 呼出し数と写しメソッド呼出し数が不一致。mask なし |
| M2 | `test_t080_shared_base_visible_output_uses_one_snapshot` | 変更後の source bytes が二回目の destination に現れる。集合検査より先に assert。mask なし |
| M3 | 同新規 test | 実関数の呼出しが 2 回になる。呼出し回数を先に assert。mask なし |
| M4 | 同新規 test | destination の mtime が写しと一致しない。mask なし |
| M5 | 同新規 test | ignored file と receipt が集合に混入する。mask なし |

変異自体は実行しておらず、帰属は静的確認です。

## 波及

所有外 caller の編集はありません。共有 fixture の実 builder 経路だけが写しを使います。`get()`・`close()`、単独走、既存の全件性検査は変更していません。新規 test は同じファイル内なので file 集合は不変、consumer helper を直接呼ばないため AST consumer 台帳の 20 node は不変です。関連 meta-test は dispatch 失敗により未実走です。

## 総括

裁定 v2 の実装と静的確認は完了しました。変更は指定の 1 ファイルのみです。テスト結果は dispatch 障害のため未確定で、親側の実走が必要です。