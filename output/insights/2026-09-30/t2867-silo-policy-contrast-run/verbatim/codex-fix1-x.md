## 総括

裁定で処置が指定された所見 1・2・3・4・6 を修正しました。既存7試験の期待値は変更せず、各所見に1試験ずつ追加しました。所有2ファイル以外は編集していません。

## 変更 file と行数

- [contrast_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py): 459行
- [test_contrast_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/test_contrast_runner.py): 295行

## 所見ごとの対応

- **1 — 排他:** [実装:421行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:421)、試験 `test_lock_rejects_second_runner_and_accepts_stale_pid`。古い PID が残っていても lock を取得できれば起動を受理する。同じ lock が保持されていれば起動を拒否し、投入前に rc=2 となる。
- **2 — 親起動前の記録:** [実装:341行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:341)、試験 `test_starting_parent_restart_requires_attention`。起動完了が記録された親の state は再読込を受理する。`starting` が残る state は `parent-start-unknown` の attention にし、親を再起動しない。
- **3 — init・submit の intent:** [実装:281行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:281)、[383行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:383)、試験 `test_leftover_init_or_submit_intent_requires_attention`。結果が保存されて intent が消えた state は再読込を受理する。init または submit の intent が残れば `intent-unknown` の attention にし、再投入しない。
- **4 — qstat の不在確認:** [実装:211行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:211)、試験 `test_job_missing_needs_two_successes_and_120_seconds`。投入から120秒以上経ち、成功した qstat で連続2回不在なら終了と受理する。それ以前の不在では job を保持し、再投入しない。
- **6 — 停止後の init:** [実装:376行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:376)、試験 `test_stop_during_open_series_prevents_next_init`。停止がなければ次の系列の init を受理する。途中で STOP が立てば後続の init を行わない。

## 試験

`python3 scratch/t2867_contrast_runner/test_contrast_runner.py -v`: **12件成功**（既存7件、追加5件）。`git diff --check` も成功しました。

## 未解決・報告して止めたこと

試験の再実走は41.2秒で、段4仕様の「合計30秒以内」を超えました。所見5・7・8には裁定どおり手を加えていません。