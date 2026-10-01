## 総括

裁定 §2 の駆動 loop を新規 2 ファイルに実装しました。既存の起動器・台帳・親・driver は変更していません。commit は作成していません。

## 変更 file と行数

- [contrast_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py): 421 行
- [test_contrast_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/test_contrast_runner.py): 195 行

## 実装した interface

CLI は `run --config <config.json>` と `status --config <config.json>` です。config key は裁定 §2.1 の指定どおりです。`runner-state/` に `state.json`、`actions.jsonl`、`attention.jsonl`、`done.json` を記録します。state は系列ごとの checkout・job request ID・親の pid と機会番号・attention・終了理由を持ちます。

## 試験

`python3 scratch/t2867_contrast_runner/test_contrast_runner.py` を実走し、**7 試験すべて成功**しました。nodeid は `RunnerTests.test_startup_validation_and_order_limit`、`test_job_not_repeated_on_qstat_failure_or_restart`、`test_dead_job_and_rc_attention_then_done`、`test_status_rc_attention_does_not_block_other_series`、`test_init_failure_keeps_schedule_order`、`test_pause_stops_new_actions`、`test_parent_limit_and_clean_environment` です。

差し替えたものは `qstat`・`qsub` の shell、checkout 内の起動器と親です。台帳モジュールは実物を一時 checkout に写して使用しました。

## 裁定 §2 の各項の対応

- §2.1 入力・設定: [contrast_runner.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:40)
- §2.2 起動時検査・pid: [contrast_runner.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:40)、[contrast_runner.py:370](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:370)
- §2.3 周回・親・系列開始・pause: [contrast_runner.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:191)、[contrast_runner.py:288](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:288)、[contrast_runner.py:325](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:325)
- §2.4 attention・記録・終了・signal・status: [contrast_runner.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:150)、[contrast_runner.py:354](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:354)
- §2.5 自己試験: [test_contrast_runner.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/test_contrast_runner.py:52)

## 未解決・報告して止めたこと

`init` が失敗した項目は attention とし、順序を守るため後続項目を開きません。この状態では全項目が開かれないため、`done.json` は生成されず、運用者の対応が必要です。