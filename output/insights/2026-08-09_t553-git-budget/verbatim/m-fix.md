実装完了です。変更は job directory 配下の2ファイルだけです。docs・repo・git 状態・scheduler には触れていません。

### 変更ファイル

- [probe_git_batch_budget.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.py:33) — 1,024行
- [job_probe_git_budget.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/job_probe_git_budget.sh:4) — 233行、mode 755

### F1 — 失敗測定の completed 化を防止

- worker 欠損を `missing_worker=true` として補完: probe 337–380、459–481行。
- 成功条件と `failed_measurements` / `timed_out_measurements` / `missing_workers` を集計: 503–523行。
- 3件を初期 JSON から必ず出力し、0件も省略しない: 801–806行。
- `completed` は全 planned worker が戻り、失敗・timeout・欠損がすべて0の場合だけ true: 1009–1020行。未完了時は probe も rc=1。
- stdout 冒頭にも除外件数を常時表示: 578–585行。

`failed_measurements` は分布から除外された全観測数で、timeout・欠損はその内訳として別記します。

### F2 — invariant の実要求数を動的導出

- `(HEAD commit数 + candidate 1件) × production path数` で既定リスト先頭を構成: 707–726行。
- candidate は対象 repo に object を書かず、HEADを1回重ねた workload proxy で同じ3 pathを再現。
- JSON の `real_invariant_requests` と derivation に commit数、`+1`、path数、`commit-tree -p HEAD` の理由を記録: 739–753行。
- `7002` / `7005` の literal はありません。
- smoke 時点の現在の HEAD は2,347 commitだったため、導出値は `(2347+1)×3=7044`。HEADがbrief時点の2,334 commitなら自動的に7,005になります。
- job の `REQUEST_COUNTS=default` は `--requests` を省略し、この動的既定値を使います: shell 97–125、212–225行。

### F3 — 大 byte・少数 request fixture

- production の上限から、32 MiB合計（16 MiB×2、R=2）と16 MiB単体（R=1）を生成: probe 264–324行。
- `git hash-object -w` の書込み先は一時 repo のみ: 296–300行。
- 一時 repo が対象 repo 配下なら拒否し、job directory に作成: 919–925行。
- fixture 測定後は `finally` で削除し、JSON にパス・削除方針・削除結果を記録: 926–971行。
- 全 measurement の `stdout_bytes` を維持。要約には `max/request` と `max/stdout_byte` を別々に表示: 526–573、590–645行。

### F4 — warm 順序偏り

- `--concurrency-order {ascending,descending}` を追加し、既定を `descending`: 65–90行。
- 各 `(kind, requests)` の group 実行順を `warmup_rank` として全 workerへ記録: 847–868行。
- page cache は落とさず、descending順もcold近似にすぎないことをJSON `limitations`へ明記: 773–788行。

### F5 — hard cap / walltime

- probe の hard cap 既定値を300秒へ変更: probe 33、71–73行。
- PBS walltime を `03:00:00` に変更: shell 4行。
- 見積根拠を shell 7–11行へ記載。標準 matrix は最大78 groupで、3時間は1 group約130秒と準備約11分。300秒は各processの暴走防止であり、cap反復時は完走扱いにしません。

### 動作確認

ログインノード `pegasus02` で許可された小規模 smoke を1回だけ実施しました。

- 指定: `--requests 1 --concurrency 1 --repeats 1 --kinds batch --hard-cap-seconds 30`
- 所要: 1.75秒
- fixture: R=2 / 32 MiB、R=1 / 16 MiB
- 結果: `completed=true`、planned/returned各2、失敗0、timeout 0、missing worker 0
- `stdout_bytes`: 33,554,544 bytes、16,777,272 bytes
- full matrix・48並列の本測定は未実走です。
- Python AST、CLI help、昇順/降順と失敗集計の静的 assertion、`bash -n` は成功。`shellcheck` は未導入です。

### 親用 qsub

```bash
qsub -l elapstim_req=03:00:00 -o /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_budget.stdout -e /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_budget.stderr -v 'PROBE_PATH=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.py,TARGET_REPO=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget,OUTPUT_JSON=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/probe_git_batch_budget.result.json,REQUEST_COUNTS=default,CONCURRENCIES=1:16:48,REPEATS=2,HARD_CAP_SECONDS=300,PROBE_KINDS=batch-check:batch:rev-list:history-log:history-ls-tree,CONCURRENCY_ORDER=descending' /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/job_probe_git_budget.sh
```

### repo非書込み確認

- 作業前後の `git status --porcelain=v1 --untracked-files=all`: 0行。
- worktree / staged の `git diff --quiet`: ともに rc=0。
- smoke 開始後に作成・更新された common object-store file: 0件。
- `hash-object -w` の宛先は job directory の一時 repoだけ。
- smoke JSONと `.git-blob-fixture-*` の残存: 0件。
- 一時 repo は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t553-git-budget/.git-blob-fixture-*` に作り、fixture測定終了時に削除します。SIGKILL等の捕捉不能終了では残り得る旨もJSONへ記録します。

## 総括

F1〜F5を指定2ファイルだけに反映しました。  
失敗・timeout・worker欠損は completed を false にし、件数を必ず記録します。  
実要求数はHEAD、candidate +1、実path数から動的に導出します。  
大blob fixtureはjob directoryの一時repoだけへ書き、測定後に削除します。  
repo・docs・git・schedulerへの書込みや操作は行っていません。