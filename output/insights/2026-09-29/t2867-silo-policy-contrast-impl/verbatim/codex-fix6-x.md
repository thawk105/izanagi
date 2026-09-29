## 総括

裁定5のX欄を実装しました。対照 preview では proposal 読込の `ValueError` を `proposal-schema`、auditor gate の失敗を `auditor-gate`、digest 不一致を `auditor-digest` として構造化出力します。compiler 不在など、対象外の異常は従来どおり例外で返します。既存テストの期待値は変更していません。

## 変更 file と行数

- [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/campaign/p3_s4_loop_policy.py:637)：追加36行、削除9行
- [test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/tests/test_p3_s4_loop_policy.py:304)：追加28行

合計73行です。

## 実装した interface

`--contrast-ledger` 付き `--preview-diff` の失敗時に、`{passed: false, working_diff: null, diff_digest: null, subtype, rule_id}` を stdout に出し、rc=1を返します。`rule_id` は例外文の先頭80字です。

## テスト

`test_contrast_preview_classifies_schema_and_digest` を追加しました。`python3 tools/run_tests.py` で実行を試みましたが、`qstat -Q` の事前確認が失敗し、**テスト本体は未実走**です。`git diff --check` は通過しました。

## 所有外への波及

構造化出力の利用先は対照 round の `check`・`finalize` です。同ファイルは変更していません。指定された inventory 用テストファイルに、対象テストファイル名への参照はありませんでした。

## 未解決・報告して止めたこと

実装済み・未実走です。dispatch infrastructure failure（rc=16）のため、親側でテストの実走確認が必要です。