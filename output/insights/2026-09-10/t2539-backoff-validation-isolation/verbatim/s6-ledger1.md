## 実行
`python3 tools/update_acceptance_duration_ledger.py --add-only /home/SFC/tanab/.claude/jobs/4edef424/tmp/t2539/junit-new.xml` — rc=0、added=19。

## 追加 node
`orchestrator/tests/test_silo_validation_isolation.py` の19 node。producer は一覧を出力しなかったため、1 command 制約下では個別名を取得していない。

## 検証
`mode=add-only`、skipped/excluded は全て0。既存 entry 保持は add-only 契約による。制約遵守のため `git status` は追加実行していない。

## 総括
台帳更新は成功。指定外 command・file 編集・commit は実施していない。