[aggregate](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-fix-2/orchestrator/campaign/silo_policy_recon.py:273) の job 識別を `(hostname, started_at)` に変更しました。初走 8 件、初走と再測、再測同士の重複をエラーにします。`pbs_jobid` は null を許し、非 null の値に限って従来の重複・一致検査を続けます。

[テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-fix-2/orchestrator/tests/test_silo_policy_recon.py:284) には、全 job の `pbs_jobid` が null でも識別子が異なれば二値が決まる正例と、再測が初走と同じ識別子なら binary null になる負例を追加しました。初走同士・再測同士の重複も検査します。既存テストの期待値は変更していません。

**所有外への波及（静的確認）:** aggregate の詳細 JSON と投影 JSON の判定結果に影響します。出力形式と `run` の計測経路は変更していません。所有外ファイルの編集はありません。

## 総括

- 変更: aggregate と対象テストのみ。commit は作成していません。
- 実走: なし。`tools/run_tests.py orchestrator/tests/test_silo_policy_recon.py -q` は `qstat -Q` の dispatch 事前確認で失敗し、子プロセスは未起動です。
- 静的確認: 両ファイルの AST 解析と `git diff --check` は通過しました。
- 未実走・リスク: テストの合否は未確認です。実走できる環境で上記テストファイルの確認が必要です。