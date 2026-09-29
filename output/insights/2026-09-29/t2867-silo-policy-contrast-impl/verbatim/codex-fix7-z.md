## 総括

裁定 6 の2点を、所有するテストだけで修正しました。変更は合計10行の増減で、実装ファイルは変更していません。

## 変更 file と行数

- [test_silo_policy_contrast_round.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/tests/test_silo_policy_contrast_round.py:103)：3行追加・3行削除。finalize の例外と、`opportunity-end` が増えないことを検査。
- [test_silo_policy_contrast_parent.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/tests/test_silo_policy_contrast_parent.py:32)：3行追加・1行削除。各起動 argv に4種類の session 引数がないことを検査。

## 実装した interface

変更なし。テストが検査する `R.finalize(...)` と `P.run_opportunity(...)` の呼び出し形も変更していません。

## テスト

`test_schema_failures_consume_one_a_and_do_not_retry` と `test_fresh_sessions_and_429_retry_same_a` を含む2ファイルを `tools/run_tests.py` で実走しようとしましたが、`qstat -Q` の事前確認で失敗し、テスト本体は未実走です。`py_compile` と `git diff --check` は通過しました。差し替え seam は既存テストの driver `run` と Claude `spawn` です。

## 所有外への波及

所有外の caller、共有 fixture、consumer test の変更はありません。指定された6つの inventory 系テストファイルを検索し、今回の2ファイルへの参照は見つかりませんでした。

## 未解決・報告して止めたこと

計算ノードへの dispatch 障害により、テストの実走結果は確認できていません。