単位 B の実装を作業木に追加しました。**実装済み・未実走**です。commit と計算 job の投入はしていません。

`_source` は従来、stock 以外の手書き本文を `prepare_policy` の 4 段検査後に書き込み、内容を照合していました。`_build_variant` は stock に `STOCK_G`、軸 ON に `GENOME` を使っていました。この経路を保ったまま、本文指定と stock の BACK_OFF=0/1 を追加しました。

[recon driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-unit-b/orchestrator/campaign/silo_policy_recon.py)、[テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-unit-b/orchestrator/tests/test_silo_policy_recon.py)、[job body](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-unit-b/tools/pegasus/silo_policy_recon_job.sh)、[投入 script](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-unit-b/tools/pegasus/submit_silo_policy_recon.sh)を新設し、8 組の `job_of`、集計、投影 JSON、既存の行番号 pin と materializer 説明を更新しました。既存 coverage／smoke の呼出しは変更していません。

Python 構文検査、`git diff --check`、`check_codex_agents.py`、`check_docs.py` は通過しました。新規テストと IR・coverage・smoke・spawn site・build authority・test file 集合の対象を `tools/run_tests.py` で起動しましたが、`qstat -Q` preflight が rc=1 となり **child_started=false** でした。したがって緑と報告できる pytest nodeid はありません。login での直接 pytest と投入 script の dry-run も PreToolUse hook に拒否されました。

静的調査で、**新 script の Pegasus admission 登録が所有範囲外**と判明しました。[admission_registry.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-unit-b/tools/pegasus/admission_registry.json) と対応する `test_hooks.py`・runbook の閉集合登録が必要です。現状、hook 経由の投入と dry-run は実行できません。また再測投入器は候補を ID 順に並べ、一度に最大 4 本まで受け付けます。次の組の投入停止判断は未自動化です。

## 総括

- 変更：所有する Python・テスト・Pegasus script、materializer 説明。commit なし。
- 実走結果：構文・差分・Codex agent・docs 検査は通過。pytest の実走 nodeid はなし。
- 未実走：4 段検査の接続試験、集計境界試験、メタテスト、script dry-run。
- リスク：`qstat -Q` 障害、所有範囲外の admission 登録、4 件超の再測組の停止判断。
- third-party cache の既定所在：`/work/1/SFC/tanab/izanagi-thirdparty-cache`。