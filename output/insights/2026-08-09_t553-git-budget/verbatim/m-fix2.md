実装完了です。変更対象は [job_probe_git_budget.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/job_probe_git_budget.sh:201) だけです。probe 本体、docs、walltime、hard cap、matrix、git 状態は変更していません。

### 変更箇所

- G1 — 252–254行、291–295行  
  共通 builder が `python3.10 -I -B "$PROBE_PATH_REAL"` の順で配列を構成。本測定もその配列を実行するため、probe path が Python の最初の位置引数になります。

- G2 — 252–262行、279–295行  
  preflight と本測定が同じ `build_probe_command` を使用。`--help` を1回実行し、argv・rcを stdout に記録。失敗時は本測定前に即終了します。

- G3 — 201–250行  
  `/etc/login.defs` の `UID_MIN`（取得不能時1000）を基準に、現在ユーザー以外を `other_regular_user_process_count` と `system_daemon_process_count` に分離。distinct UID数とユーザー別一覧も出力します。

### 検証

`bash -n`：

```text
bash_n_rc=0
```

実 probe の軽量 preflight：

```text
actual_probe_help_rc=0
```

`/bin/true` を Python 代替にして測定を起動しなかった argv dry-run の逐語です。

```text
preflight_argv= python3.10 -I -B /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.py --help
preflight_rc=0
probe_argv= python3.10 -I -B /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.py --repo /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget --out /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/.t553-argv-dryrun.yzFZlS/probe-result.json --repeats 2 --hard-cap-seconds 300 --concurrency-order descending --kinds batch-check batch rev-list history-log history-ls-tree --concurrency 1 --concurrency 16 --concurrency 48
probe_rc=0 job_rc=0
dryrun_rc=0
```

失敗系では次を確認しました。

```text
preflight_rc=1
probe_rc=1 job_rc=1
failure_dryrun_rc=1
failure_started_measurement=no
```

`shellcheck` は未導入のため未実行です。`qsub`・`qstat`・`qdel`・本測定は実行していません。

### 親用 qsub

```bash
qsub -l elapstim_req=03:00:00 -o /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_budget.stdout -e /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_budget.stderr -v 'PROBE_PATH=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.py,TARGET_REPO=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget,OUTPUT_JSON=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.result.json,REQUEST_COUNTS=default,CONCURRENCIES=1:16:48,REPEATS=2,HARD_CAP_SECONDS=300,PROBE_KINDS=batch-check:batch:rev-list:history-log:history-ls-tree,CONCURRENCY_ORDER=descending' /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/job_probe_git_budget.sh
```

### repo 非書込み確認

`GIT_OPTIONAL_LOCKS=0` で作業前後の status、unstaged diff、staged diffを比較しました。

```text
repo_status_before_after_cmp_rc=0
repo_diff_before_after_cmp_rc=0
repo_cached_before_after_cmp_rc=0
repo_status_after_begin
repo_status_after_end
```

作業前は3対象とも空で、作業後も同一です。dry-run用ディレクトリも残っていません。commitやgit状態変更は行っていません。

## 総括

G1でprobe pathをPython argvへ追加しました。  
G2で同じbuilderを通る一回限りのpreflightを追加しました。  
G3で一般ユーザーとsystem daemonのprocess数を分離しました。  
repo・docs・scheduler・本測定には触れていません。