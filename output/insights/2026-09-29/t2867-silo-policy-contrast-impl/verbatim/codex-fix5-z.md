## 総括

所見1・2を所有4ファイルで修正しました。round は不正な coder・auditor 出力と構造化 JSON を返さない preview を、同じ a の `rejected` として一度だけ記録します。親は保存済み attempt の最大番号と `exit.json` の失敗回数を引き継ぎます。変更は追加106行・削除14行の計120行で、commit は作っていません。

## 変更 file と行数

| file | 追加 / 削除 |
|---|---:|
| [round](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/tools/silo_policy_contrast_round.py:152) | 58 / 12 |
| [parent](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/tools/pegasus/silo_policy_contrast_parent.py:31) | 5 / 1 |
| [round テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/tests/test_silo_policy_contrast_round.py:82) | 27 / 1 |
| [parent テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/tests/test_silo_policy_contrast_parent.py:73) | 16 / 0 |

## 実装した interface

`check(...)` と `finalize(...)` は schema 不合格時に `{"status": "rejected"}` を返し、`opportunity-end` に `coder-schema` または `auditor-schema` と短い `reject_rule_id` を記録します。既存の構造化 preview 拒否の扱いは維持しました。`run_opportunity(...)` の公開 signature は変更していません。

## テスト

追加した `test_schema_failures_consume_one_a_and_do_not_retry` と `test_restart_uses_next_attempt_and_prior_failures` を含む2ファイルを `tools/run_tests.py` に指定しましたが、qstat preflight 失敗（rc=16）で子テストは起動せず、**未実走**です。4ファイルの構文確認、`git diff --check`、`check_codex_agents.py` は通過しました。

## 所有外への波及

指定された inventory テスト群に、この2ツールへの参照は見つかりませんでした。所有外の file は編集していません。

## 未解決・報告して止めたこと

テストの実走確認が残っています。`check_docs.py` は所有外の `docs/phase3-silo-policy-runbook.md:210` にある未作成パス参照を1件報告しました。