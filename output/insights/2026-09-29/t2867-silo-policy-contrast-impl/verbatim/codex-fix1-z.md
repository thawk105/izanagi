## 総括

所有する 7 file に、F3・F4・F5・F8・F9・F11・F13・F14 の修正を入れました。F15 は一部のみ実装済みです。指定の 6 件を含むテストは、dispatch 前の `qstat -Q` エラーで実走できていません。

## 変更 file と行数

追加／削除行数は次のとおりです。

| File | ＋／－ |
|---|---:|
| [round tool](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/tools/silo_policy_contrast_round.py) | 26／7 |
| [親](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/tools/pegasus/silo_policy_contrast_parent.py) | 14／5 |
| [親の指示文](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/tools/pegasus/silo_policy_contrast_parent.md) | 3／4 |
| [report](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/campaign/silo_policy_contrast_report.py) | 25／8 |
| [round test](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/tests/test_silo_policy_contrast_round.py) | 10／9 |
| [parent test](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/tests/test_silo_policy_contrast_parent.py) | 9／7 |
| [report test](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/tests/test_silo_policy_contrast_report.py) | 27／11 |

## 実装した interface

`finalize(..., *, ledger_root, run=...)` は完成した `{coder, auditor}` を driver で preview し、拒否時は同じ proposal file で `--record-reject` を呼び、`reject_subtype`・`reject_rule_id` 付きの `opportunity-end rejected` を記録します。`prepare` は `open_opportunity`・`next_opportunity` を使い、critic の各結果行に指定の性能・品質項目を載せます。

親は各起動後に増えた `proposed`／`rejected` だけを成功と認め、それが無ければ `empty` を記録します。report は `series_state` の A・B・未終端 slot を使い、score の variant・source digest を固定 endpoint と照合し、arm ごとの A 使用数と拒否内訳を出します。

## テスト

3 test file の台帳 fixture を `ContrastLedger.create/append` に変更しました。`python3 tools/run_tests.py` による指定 3 file の実行は **子プロセス起動前に失敗**しました（`qstat -Q preflight rc=1`）。6 件が緑になったとは報告できません。変更した Python 6 file の構文解析と `git diff --check` は通過しました。

## 所有外への波及

`open_opportunity`・`next_opportunity` は子 Y が追加する予定の API に依存します。driver の完成 proposal preview は子 X の変更に依存します。指定された inventory test 群の静的検索では、今回の file 名に一致する項目はありませんでした。既存 round test の driver 呼出しと親 test の Claude 起動には seam があります。

## 変異の位置

- M12: [report の探索点判定](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/campaign/silo_policy_contrast_report.py:115) → `test_seed_only_does_not_count_as_generation`
- M13: [族別 Holm](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/campaign/silo_policy_contrast_report.py:200) → `test_holm_is_adjusted_within_each_two_comparison_family`
- M14: [新規起動 argv](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/tools/pegasus/silo_policy_contrast_parent.py:45) → `test_fresh_sessions_and_429_retry_same_a`

## 未解決・報告して止めたこと

**F15 は未完了です。** 親自身が書く `empty`・`outage`・`role-failure` の終端には、`out.json.modelUsage` の key を `models` として記録します。一方、`proposed`・`rejected` は round が Claude 起動中に immutable な台帳へ書き、当該起動の `out.json` は終了後に初めて確定します。現行の event 書込み順では、その終端へ実測 model ID を載せられません。親で終端を確定する等の契約変更が必要です。