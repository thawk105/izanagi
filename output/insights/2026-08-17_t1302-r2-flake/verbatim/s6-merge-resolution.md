## 解消の方針

[tools/dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1302-r2-nonattrib/tools/dev_wave_wait.py) の競合 marker のみを除去し、HEAD 側の receipt 検証関数の後へ main 側の retry 補助関数を配置しました。

## 両側の保全

- HEAD 側: `_red_check_payload_nodeids`、`_verify_red_check_receipt` からの呼出
- main 側: `_NoVerdictLogEvidence`、`_inspect_no_verdict_log`、`_retry_archive_path`、`_archive_retry_log`、`_renew_retry_lease`、`_print_attempt_journal`
- retry 経路: `_run_acceptance_attempt` から各補助関数、`run_acceptance` から attempt 再試行
- 両親の定義と AST 単位で一致することを確認済み

## 確認したこと

- 指定の `ast.parse` 構文確認: 成功
- module import: 成功
- conflict marker 3 種: 残存なし
- top-level 定義重複: なし
- `git diff --check`: 成功
- pytest: 未実走
- `git add` は sandbox 外の read-only index により失敗したため、Git status は `UU` のままです。親側で `git add tools/dev_wave_wait.py` が必要です。
- docs・他ファイルの編集、commit は行っていません。

## 総括

作業ツリー上の競合は、両側の意味を保って解消済みです。  
構文・import・呼出経路・重複定義・marker 不在を確認しました。  
pytest は規律どおり未実走です。  
index 登録のみ sandbox 制約で未完了です。