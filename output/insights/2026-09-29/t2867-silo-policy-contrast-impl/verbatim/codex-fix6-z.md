## 総括

Z担当の P1・P2 を実装しました。`check` と `finalize` は、driver の構造化 JSON が `passed=false` の場合だけ却下を記録し、`subtype`・`rule_id` をそのまま保存します。JSON のない非0終了は終端を記録せず例外にします。

## 変更 file と行数

- [silo_policy_contrast_round.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/tools/silo_policy_contrast_round.py:62)：追加22行・削除26行
- [test_silo_policy_contrast_round.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/tests/test_silo_policy_contrast_round.py:111)：追加33行

合計79行です。

## 実装した interface

`check(...)`・`finalize(...)` の signature は変更していません。内部関数 `_require_preview(result)` と `_record_preview_reject(ledger, ledger_root, a, proposal, data, run)` を追加しました。

## テスト

`test_preview_failure_classification` を追加しました。`check`・`finalize` それぞれの異常終了と構造化却下を扱います。`py_compile` と `git diff --check` は通過しました。`run_tests.py` は Pegasus の `qstat -Q` 前確認で `rc=16` となり、**テスト本体は未実走**です。

## 所有外への波及

driver の構造化拒否出力と台帳の `opportunity-end` を使用します。指定の inventory 対象6ファイルに、round への参照は見つかりませんでした。所有外のファイルは変更していません。

## 未解決・報告して止めたこと

既存の `test_schema_failures_consume_one_a_and_do_not_retry` には、driver の非構造化エラーを `auditor-schema` 却下とする期待値が残っています。今回の裁定とは食い違いますが、指示に従い期待値を変更していません。