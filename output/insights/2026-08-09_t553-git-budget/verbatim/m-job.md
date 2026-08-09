作成しました。

- ファイル: [job_probe_git_budget.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/job_probe_git_budget.sh)
- 行数: 215 行
- mode: `755`
- `bash -n`: 成功
- `shellcheck`: 環境に未導入のため未実行
- `qsub`、`qstat`、`qdel`、probe は実行していません。

親がそのまま実行できる投入コマンドです。

```bash
qsub -o /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_budget.stdout -e /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_budget.stderr -v 'PROBE_PATH=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.py,TARGET_REPO=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget,OUTPUT_JSON=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.result.json,REQUEST_COUNTS=7002:10000:25000:50000,CONCURRENCIES=1:16:48,REPEATS=2,HARD_CAP_SECONDS=600,PROBE_KINDS=batch-check:batch:rev-list:history-log:history-ls-tree' /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/job_probe_git_budget.sh
```

walltime は `16:00:00` です。上記入力では batch-check が `4要求数 × 3並列度 × 2 repeats = 24 group`、batch も最大24 group、固定3 kind が18 groupで、最大66 groupです。各 group の probe 内上限は hard cap 600秒＋回収猶予90秒なので約12時間39分となり、準備、JSON更新、終了処理の余裕を加えました。

逐語再利用元は次のとおりです。

- `tools/pegasus/floor_campaign.sh`: PBS directive の配置と `#PBS -A SFC`、`#PBS -q gen_S`、`#PBS -b 1`、`set -Eeuo pipefail`、`umask 077`、`PBS_JOBID` 検査、`unset PYTHONPATH PYTHONHOME PYTHONSTARTUP`
- `tools/pegasus/submit_floor.sh`: 単一の `-v` export specificationを使い、job script を末尾に置く `qsub -v "$export_spec" "$JOB_SCRIPT"` インタフェース

repo 無変更は、作成前後に `git --no-optional-locks status --porcelain=v1 --untracked-files=all` がともに空であること、および最後に staged/unstaged 両方の `git diff --quiet` が成功したことで確認しました。

## 総括

M2 の PBS job script 1本だけを repo 外へ作成しました。  
計算ノード情報、他ユーザー process 数、marker、probe/job rc を記録します。  
全 probe 入力は `qsub -v` 必須で、対象 repo 内の出力は拒否します。  
repo・docs・git 状態には変更を加えていません。