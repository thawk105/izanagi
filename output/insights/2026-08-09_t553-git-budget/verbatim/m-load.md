実装完了です。

- 作成: [job_probe_under_load.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/job_probe_under_load.sh) — 1,026 行、mode 755
- 既存 `probe_git_batch_budget.py` は変更していません。
- 負荷源は第一候補の `python3.10 tools/run_tests.py -n 48`。`--help` と実装を確認し、計算ノードでは local 実行になる構成と判断しました。pytest worker が開始されず runner が停止・dispatch 等した場合、出力を逐語記録して直接 `python3.10 -m pytest ... -n 48 --dist loadgroup` へ縮退します。
- pytest の rc は JSON/marker に記録しますが、job rc には使用しません。

親がそのまま投入できる一行です。

```bash
qsub -o /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/job_probe_under_load.stdout -e /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/job_probe_under_load.stderr -v PROBE_PATH=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.py,TARGET_REPO=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget,OUTPUT_JSON=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_under_load.result.json,LOAD_LOG=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/pytest_under_load.log,HARD_CAP_SECONDS=600,SAMPLE_INTERVAL_SECONDS=15,BEFORE_CYCLES=3,AFTER_CYCLES=3,PYTEST_WORKERS=48 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/job_probe_under_load.sh
```

walltime は `01:30:00`。全走実測 1,055〜1,408 秒に、preflight、前後各3周期、worker 起動、JSON 永続化を加えても通常は30分弱の想定です。600秒 hard cap に複数 sample が達する異常時は、予約時間を多く消費し得ます。

検査結果:

- `bash -n`: 通過
- 埋め込み Python AST parse: 通過
- 失敗・timeout sample の集計除外テスト: 通過
- PBS queue/node/walltime、48 workers、必須sample field、scheduler command不在、機体固有path literal不在: 通過
- ログインノードでは pytest・probe本走を未実行
- repo確認: `GIT_OPTIONAL_LOCKS=0 git status --porcelain=v1 --untracked-files=all` は空、`git diff --exit-code` は rc=0、未追跡一覧も空

この測定でも、他ユーザーの外乱は観測できても制御できません。また、別ノード、別時間帯、将来のfilesystem状態は測れません。

## 総括

- M5用PBS job scriptを1本作成しました。
- pytest全走48 worker中にproduction同形git argvを逐次測定します。
- before/during/after、失敗除外、600秒hard cap、marker記録を実装済みです。
- repo・docs・git状態は変更していません。