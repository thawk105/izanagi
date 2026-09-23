R2用の追加実装を完了しました。変更は所有3ファイルのみです。作業worktreeでの `git add`・`git commit` は行っていません。計算ノードでのpair本走は **実装済み・未実走** です。

**ファイル別の変更**

- [runner](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/t2273_replica_runner.py:243)：`pair` を追加。smoke → A2 → staging → X、別session、各走前後のclean・HEAD・単独性・loadavg、A2/Xの資源標本、2900秒alarmを実装しました。失敗時は `incomplete.json` を残します。既存の `run` は保持しています。
- [plugin](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/t2273_replica_plugin.py:171)：実repo rootとのresolve比較で複製元だけを差し替え、実関数を呼びます。spanに元source・staged root・`substituted`・対照介入の明記と、戻り値の件数・sorted集合のSHA-256を追加しました。
- [analyzer](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/t2273_replica_analyze.py:668)：`--pair-dir` とJSON/Markdown出力を追加。成功した全builder（非共有も含む）を比較し、意図的な失敗は例外記録とoutcome比較に残します。単走解析も保持しています。

**stagingと可視集合の根拠**

[独立clone](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/t2273_replica_runner.py:294) は `clone --no-local --no-checkout` → 観測HEADの `checkout … -- output` です。実repoへworktree登録せず、object alternatesも作りません。

[ignore規則](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/t2273_replica_runner.py:298) はroot・output配下の `.gitignore`、`info/exclude` のbytesを保存し、local ignore設定も照合します。Git環境は実関数と同じglobal/system設定無効化です。local `core.excludesfile` がある場合は解釈を推測せず停止します。

[集合照合](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273-probe/tools/t2273_replica_runner.py:332) では実関数と同じ `ls-files` 引数の結果、可視集合、regular-file条件、各fileのbytesを比較します。可視untracked outputは**写さずXを停止**します。未コミット入力を黙って欠落させないためです。開始・終了・壁時間・件数・command・エラーは `staging.json` に残します。

**pairのargv/env**

A2/Xとも以下を使用し、`acceptance_shards.create_session(repo, 3)` を各1回呼びます。

```text
python3.10 <repo>/tools/run_tests.py orchestrator/tests
-n 48 --dist loadgroup
--junitxml=<各session>/shard-0/junit.xml
-p tools.acceptance_shards
-p no:cacheprovider -p t2273_replica_plugin
```

共通envは既存の除去リスト適用後、以下です。

```text
PYTHONDONTWRITEBYTECODE=1
IZANAGI_TASK_RUN_AUTO_RECORD=0
PYTHONPATH=<probe>:<repo>
TMPDIR=<継承値。未設定時のみ既定値>
T2273_REPLICA_OUT=<out>/A2 または <out>/X
IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1=
  {"session_root":"<各session>","shard_count":3,"shard_index":0}
```

`T2273_LOCAL_OUTPUT_SOURCE=<staged root>` はXだけに渡します。

**対比較の主要出力key**

```text
validity, metrics_s, workers, builders,
critical_worker_decomposition, X_maximum_worker, X_largest_component,
staging, staging_wall_s,
delta_W_0_s, delta_W_0_fraction, delta_W_0_minus_staging_s,
D357_classification, builder_copy_shorter_all, recommendation,
resource_sampling, visible_copies, outcomes, guards, span_exceptions,
missing, complete_observation
```

`metrics_s` はW₀・O_max・L・pre・postのA2/X/差、`builders` はbuild・copy・copy.list・copy.copytree・git・issueのA2/X/差です。資源欠測は有効性と分けて表示し、完全観測でなければCLIはrc 1です。

**loginでの実走結果（pegasus02）**

- 両CLIの `python3 -B tools/t2273_replica_{runner,analyze}.py --help`：各rc 0。
- runnerの `pair --repo-root "$PWD" --probe-dir "$PWD/tools" --out-root /tmp/t2273-login-guard-r2 --job-tag login-guard`：hostname防壁でrc 3。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/tools:$PWD" python3 -B /tmp/t2273-r2-check.py`：rc 0。[検証script](/tmp/t2273-r2-check.py) は実 `analyze_pair()`・`analyze()`・`stage_output()` を呼び、依存先のstubは使用していません。
  - 正例：ΔW₀=10秒、25%、staging控除後7秒、Δcopy=2秒。
  - 負例：digest・outcome不一致、dirty、others、record-errorを拒否。
  - 小さい一時git repo：集合・bytes一致、ignore規則、独立admin、untracked拒否を確認。
- inline検証：Python 3.10構文、実 `Recorder.invoke()` の件数・digest記録を確認。
- 実R1の `--run-dir …/job-out-r1/A` 再解析：rc 1。既存の `shard`・`missing` と一致し、資源counter欠測のみでした。
- `git diff --check`：rc 0。

実test moduleの直接importはhold防壁に拒否され、解除していません。実copy関数へのplugin接続と48-worker本走は未実走です。Xが後走のwarmを受ける偏り、独立cloneとbytes照合のstaging費用、実TMPDIRの局所性確認が残ります。

最終 `git status --porcelain`：

```text
 M tools/t2273_replica_analyze.py
 M tools/t2273_replica_plugin.py
 M tools/t2273_replica_runner.py
```

## 総括

3ファイルのR2実装と、合成正例・負例、小repo staging検証を完了しました。
実R1の単走解析結果は維持されています。
計算ノードのpair本走とplugin実接続は、実装済み・未実走です。
親は最初にsmoke、TMPDIRの局所性、staging一致、A2/X全builderのdigest・record-errorを確認してください。