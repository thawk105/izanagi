結論は「生死確認は実施してよいが、恒久実装は現時点では NO-GO」です。必須ファイルはすべて読めました。以下は静的読解によるプランであり、pytest・qsub・flock 実測は行っていません。

## 静的確認と親 brief の訂正

確認できた事実:

- 現台帳は 41 変異、`runner_mode=dispatch`、全走コマンドで、変異時間合計 19,036.567 秒、中央値 467.045 秒、baseline 277.766 秒、collection 226.653 秒。
- `bnode*` は `PEGASUS_COMPUTE` になり、compute 上の `run_tests.py` は再 dispatch せず local pytest へ進む。`orchestrator/campaign/site_policy.py:29-45`、`tools/run_tests.py:928-1004`。
- 現在の実走回数は fresh run なら collection + baseline + mutations の `N+2`。ただし harness の表示見積りは collection を数えておらず `N+1` になっている。`tools/mutation_harness.py:1951-1964`。
- `output/pegasus-dispatch/` は `.gitignore:25` で無視される。

親 brief の誤り:

1. `test_output_tail` から対応できる n=12 の pytest 時間中央値は 237 秒ではなく、通常の偶数中央値で `(239.40+240.59)/2 = 239.995 秒`。対応レコードごとの overhead 中央値 229.856 秒と、約 2.75 h/matrix という結論はほぼ正しい。
2. `mutation` task 追加は閉じた enum の既存パターンには沿うが、「既裁定へそのまま乗る」は誤り。D105 は集合を明示的に `{"tests","provenance"}` へ固定し、D117 は第 3 task に D105 の supersede、子側 env allowlist 強制、artifact/cwd/rc 契約を要求している。`docs/decisions.md:4710-4714,5551-5556`。
3. 「walltime 切断は `--resume` で回収」は不十分。SIGKILL 後に対象が変異済みなら、次回は起動時の HEAD-byte 検査で停止し、resume まで到達しない。既存テスト自身も SIGKILL 後に変異が残ることを固定している。`orchestrator/tests/test_mutation_harness.py:782-812`。
4. `--detached` を scheduler job 内でそのまま使うと、「外側時間上限なし」という現在の宣言と walltime が矛盾する。`tools/mutation_harness.py:1857-1896`。
5. 「lock 保証が実質ゼロ」は過大表現。コード上は同一 node の同一 `/tmp` 内では残る。ただし異なる bnode 間では効かず、sanctioned 経路の単一走行保証としては不足する。
6. gen_S の 86,400 秒上限、Lustre の `flock` mount option、NQSV の walltime signal は親の実測報告であり、この静的調査では未確認。

## A. 生死確認（DW-G01）

### 小 spec

現 HEAD に anchor が一意に存在し、過去台帳でも単独 KILL 済みの次の 3 件を使う。現行コードでも fixture が各 gate だけを発火させている。

| ID | 変異位置 | old 逐語 | new 逐語 | 期待 node |
|---|---|---|---|---|
| G01-N01 | `tools/spool_fold.py:608` | `    if path.name != expected:` | `    if False and path.name != expected:` | `orchestrator/tests/test_spool_fold.py::test_n01_frontmatter_filename_mismatch_is_rejected` |
| G01-N03 | `tools/spool_fold.py:729` | `        if symbol.key in seen:` | `        if False and symbol.key in seen:` | `orchestrator/tests/test_spool_fold.py::test_n03_duplicate_symbol_definition_is_rejected` |
| G01-N04 | `tools/spool_fold.py:744` | `            if brace >= 0:` | `            if False and brace >= 0:` | `orchestrator/tests/test_spool_fold.py::test_n04_malformed_placeholder_residue_is_rejected` |

根拠は `orchestrator/tests/test_spool_fold.py:341-376`。N01 は filename 以外を正しくした fixture、N03 は同一 key の重複だけ、N04 は正規表現に一致しない underscore 付き placeholder の残留だけを作る。いずれも当該 guard を消すと `issues=[]` になり、期待 node が赤くなる。

spec は repo 外の新規 directory に置き、例えば以下とする。

- `estimated_run_seconds: 30`
- `timeout_seconds: 300`
- `hang_timeout_seconds: 60`
- 3 件とも `category: negative`、`expected_status: KILLED`、`hang_risk: false`

### 具体的な二走手順

1. 専用 worktree が clean であることを確認し、HEAD を `anchor.txt` に保存する。probe root は共有 FS の `/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01-<nonce>/` に新設する。`/tmp` や repo 内は使わない。

2. `spec.json` を書いた直後に `sha256sum` し、得た 64 桁を固定値として両 invocation に貼る。二走の間に spec を再生成しない。各 out は別名かつ未存在でなければならない。

3. test command は両方で byte-for-byte 同じにする。

```text
/usr/bin/python3.10 tools/run_tests.py
orchestrator/tests/test_spool_fold.py::test_n01_frontmatter_filename_mismatch_is_rejected
orchestrator/tests/test_spool_fold.py::test_n03_duplicate_symbol_definition_is_rejected
orchestrator/tests/test_spool_fold.py::test_n04_malformed_placeholder_residue_is_rejected
-n 0 -rf -p no:cacheprovider
```

harness と runner の Python は同一実体でなければならないため、両方とも `/usr/bin/python3.10` に固定する。`tools/mutation_harness.py:436-444`。

4. 個別 dispatch 走は、外側 tool timeout のない node 固定 tmux/background wrapper から実行する。

```text
/usr/bin/python3.10 tools/mutation_harness.py
  --repo <absolute-repo>
  --spec <probe-root>/spec.json
  --expected-spec-sha256 <fixed-sha>
  --out <probe-root>/dispatch-ledger.json
  --runner-mode dispatch
  --detached
  -- <上記 test command>
```

開始前に `dispatch-ledger.json` が存在しないことを確認する。失敗時に同じ out を再利用せず、新しい probe root を作る。

5. dispatch 走終了後、二走目の前に以下をすべて確認する。

- wrapper rc が 0。
- ledger の `repo_head` が anchor、`spec_sha256` が固定 SHA。
- baseline が `PASSED`。
- `git rev-parse HEAD` が anchor。
- `git diff --exit-code <anchor> -- tools/spool_fold.py` が差分なし。
- `git status --porcelain=v1 --untracked-files=all --ignore-submodules=none` が空。

差分があれば束ね走へ進まず、残存 harness を停止してから DW-O19 に従い `git diff` を保存し、`git checkout -- tools/spool_fold.py`、HEAD blob との byte 一致まで確認する。

6. 束ね走は repo 外の 100 行未満の qsub script から行う。概形は次のとおり。

```bash
#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -b 1
#PBS -l elapstim_req=00:20:00
#PBS -N izdw-g01-bundle
set -u

REPO=<absolute-repo>
ROOT=<absolute-probe-root>
ANCHOR=<fixed-anchor>
SPEC_SHA=<fixed-spec-sha>
PY=/usr/bin/python3.10

unset PYTHONHOME PYTHONPATH PYTEST_ADDOPTS
unset IZANAGI_TASK_RUN_ID IZANAGI_TASK_RUNS_ROOT IZANAGI_TASK_RUN_SIDECAR
export TMPDIR=/tmp
export PATH=/usr/bin:/bin

[[ "$(hostname)" =~ ^bnode[0-9]+([.].*)?$ ]] || exit 16
"$PY" -c 'import pytest, xdist, packaging' || exit 16
cd "$REPO" || exit 16
test "$(git rev-parse HEAD)" = "$ANCHOR" || exit 16
test -z "$(git status --porcelain=v1 --untracked-files=all --ignore-submodules=none)" || exit 16
test ! -e "$ROOT/local-ledger.json" || exit 16

"$PY" tools/mutation_harness.py \
  --repo "$REPO" \
  --spec "$ROOT/spec.json" \
  --expected-spec-sha256 "$SPEC_SHA" \
  --out "$ROOT/local-ledger.json" \
  --runner-mode local \
  --detached \
  -- "$PY" tools/run_tests.py \
  orchestrator/tests/test_spool_fold.py::test_n01_frontmatter_filename_mismatch_is_rejected \
  orchestrator/tests/test_spool_fold.py::test_n03_duplicate_symbol_definition_is_rejected \
  orchestrator/tests/test_spool_fold.py::test_n04_malformed_placeholder_residue_is_rejected \
  -n 0 -rf -p no:cacheprovider
child_rc=$?

git diff --quiet "$ANCHOR" -- || child_rc=90
test -z "$(git status --porcelain=v1 --untracked-files=all --ignore-submodules=none)" \
  || child_rc=91
tmp="$ROOT/local.rc.tmp.$$"
printf '%s\n' "$child_rc" >"$tmp"
mv "$tmp" "$ROOT/local.rc"
exit "$child_rc"
```

ここでの `--detached` は現行 harness を通すための G01 限定措置であり、恒久仕様として正しいとは扱わない。

7. 二台帳から次だけを同じ順で射影し、完全一致を要求する。

```jq
[.mutations[] | {id, status, failed_nodes, matches_expectation}]
```

さらに両方で `repo_head`、`spec_sha256`、record 数 3、baseline `PASSED` を確認する。runner identity、runner mode、per-record receipt path は経路差なので比較対象にしない。

### test_command を絞る判断

推奨は上記 3 node への限定走である。G01 の目的は transport 変更による verdict 一致であり、全走を二系統で 5 回ずつ回す費用は目的に対して過大である。

限定走で確認できるもの:

- collection と expected node 実在確認
- baseline
- 逐次注入・復元
- dispatch stdout と local stdout の failed-node 解釈
- `status / failed_nodes / matches_expectation` の同値性

確認できなくなるもの:

- 全走時に追加で赤くなる node の一致
- xdist 48 worker、real-repo group、長大 stdout の影響
- cross-test interaction
- 約 240 秒の全走を `N+2` 回継続できること

したがって G01 は限定走、恒久実装後の変異本走と受入は従来どおり無指定全走
`tools/run_tests.py -rf -p no:cacheprovider` とする。

### 残るファイル

成功後に残るものは次のとおり。

- repo 内・gitignore 下: `output/pegasus-dispatch/<nonce>/` の request、probe、dispatch.sh、marker、result、receipt、`.o/.e`。
- probe root: spec、SHA、anchor、二台帳、wrapper/qsub script、rc、scheduler stdout/stderr、比較結果。
- node-local: `/tmp/izanagi-mutation-<hash>.lock`、pytest temp。lock file は fd 解放後も空 inode が残り得る。
- 残さないもの: task-run 記録。上記のとおり `IZANAGI_TASK_RUN_*` を明示 unset する。
- `.pytest_cache` は plugin 無効化、対象側 bytecode は `PYTHONDONTWRITEBYTECODE` と purge により残さない。

## B. 恒久実装（上記一致後だけ）

### B1. `mutation` task と二層 fail-closed

`tools/pegasus/dispatch_compute.py:44-73` に次を追加する。

```python
"mutation": _TaskSpec(
    child_script=("tools", "mutation_harness.py"),
    env_allowlist=frozenset({
        "GIT_CONFIG_NOSYSTEM",
        "IZANAGI_TEST_NPROC",
        "IZANAGI_TEST_TRIGGER",
        "IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS",
    }),
    probe_imports=("pytest", "xdist", "packaging"),
)
```

環境の分類:

- harness 自身: 必須 caller env はない。`GIT_TERMINAL_PROMPT=0` は自分で設定する。`GIT_CONFIG_NOSYSTEM` だけ既存 git 隔離の任意入力として通す。
- inner `run_tests.py`: `IZANAGI_TEST_NPROC`、`IZANAGI_TEST_TRIGGER`、`IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS`。
- 通さないもの: `PYTEST_ADDOPTS` と `PYTHON*` は harness が除去する。`IZANAGI_TASK_RUN_*` は dispatcher が既に三層で除去する。
- `git` は import ではないため `probe_imports` には入らない。可能なら `_TaskSpec` に executable probe を加え、mutation task だけ `git` の実在も bootstrap 段で検査する。

`tools/pegasus/dispatch_compute.py:452-498` では、現在の型検査に加えて次を子側でも行う。

- `set(requested_env) <= spec.env_allowlist`
- task-specific argv 検査
- request の `repo_root` と argv の `--repo` が同一 absolute realpath
- `--runner-mode local`
- spec/out が absolute、repo 外、共有永続 FS 上
- mutation task では nested `--runner-mode dispatch` を拒否

同じ検査を `tools/pegasus/dispatch_compute.py:935-1027` の親側で qsub 前に行う。親と子が同じ helper を呼ぶ形なら、一箇所の gate で二層を一致させられる。

`_job_script()` の `cd "$REPO"`（同:402-409）と harness の absolute `--repo` は矛盾しない。cwd は inner relative test path の基準、absolute `--repo` は対象 checkout の identity である。`_job_run()` でも `os.chdir(repo_root)` を維持する。

child rc は次で固定する。

- 0: 全 terminal record が期待一致
- 1: 完走したが期待不一致
- 2: harness 契約・evidence failure
- 3: 自己 deadline により clean に中断し、resume が必要
- 16: dispatcher infrastructure failure のみ

request v2 の `args` は JSON file に入るので shell/ARG_MAX 問題はない。ただし現状は無制限であるため、そのまま無検査では載せない。

- 最大 256 要素、各 4 KiB、総 UTF-8 64 KiB程度
- NUL、改行、制御文字を拒否
- required option は exactly one
- `--expected-spec-sha256` は 64 桁 lowercase hex
- inner `--` は exactly one、以後 nonempty
- mutation task の `--detached` と scheduler 内部 flag は caller から拒否
- `--resume` は任意
- `/tmp`、`/scr`、repo 内の spec/out を拒否

request schema v2 は維持できる。mutation task は過去の in-flight request が存在しないため、追加 field は同 task だけ必須にでき、v1 tests 互換も維持できる。

### Walltime

`tools/mutation_harness.py:1951-1964` の fresh run 数を `N+2` に修正する。

推奨要求時間:

```text
ceil((mutation_count + 2) × spec.estimated_run_seconds × 1.5 + 600)
```

`estimated_run_seconds` は dispatch duration ではなく、compute-local 全走の保守値にする。例えば 300 秒なら 41 変異で約 19,950 秒、5:32:30 なので 5:40:00 程度。

併せて次の hard bound も計算する。

```text
2 × timeout_seconds
+ Σ(hang_risk ? hang_timeout_seconds : timeout_seconds)
+ 15 × (N+2)
+ 600
```

これが gen_S 上限を超える spec は、一ジョブ形として qsub 前に拒否する。86,400 秒は投入時に `qstat -Qf gen_S` で再確認し、文書値だけを信じない。既存 t243 spec の `estimated_run_seconds=15000` は現コードの「per-run」解釈では 24 h を大幅に超えるため、自動 walltime 入力には流用できない。

`queue_wait_timeout=900` は RUN 前だけなので、長時間ジョブでも安全性上は据え置き可。混雑時に 15 分で諦める運用判断である。`overall_grace=300` も scheduler 状態反映用として据え置けるが、現在の

```python
total_deadline = submitted_at + walltime_s + overall_grace_s
```

は queue 待ちを実行 walltime から差し引いてしまう。`tools/pegasus/dispatch_compute.py:1180-1222` を最低でも次へ変える。

```python
total_deadline = (
    submitted_at
    + queue_wait_timeout_s
    + walltime_s
    + overall_grace_s
)
```

これで login dispatcher が scheduler walltime より先に active mutation を qdel する経路を閉じる。

### B2. flock の有効範囲

`tools/mutation_harness.py:1814-1835` の `/tmp` lock を authoritative lock にしてはならない。

採用案は (a) 共有 FS lock、(b) は移行補助のみとする。

- Git common dir を解決し、その checkout の外側、例えば main repo の兄弟
  `/work/.../.izanagi-mutation-locks/` に root を置く。
- lock key は strict-resolved repo path の SHA-256。現行同様、worktree ごとに一つ。
- directory は symlink 不可・0700、file は `O_NOFOLLOW|O_CREAT`・0600。
- lock file は release 時に unlink しない。待ち手が旧 inode、新規 inodeへ分裂する raceを避ける。
- `_assert_runtime_artifacts_outside_repo()`（同:585-602）で shared lock と legacy lock の両方を検査する。

移行期間は composite lock とする。

1. harness は shared lock を取得。
2. 同じ node の古い process を検出するため、現行 `/tmp` legacy lock も取得。
3. どちらかに失敗したら、取得済み fd をすべて閉じて停止。
4. login 側 mutation launcher も legacy `/tmp` lock を qsub 前から receipt 完了まで保持する。ただしこれは古い login process との同居対策であり、authoritative guarantee ではない。

古い binary が別 login/bnode で legacy `/tmp` だけを保持している場合、新コードから検出する方法はない。したがって land 前に 3 login node の既存 harness、qstat 上の mutation job、partial ledger を drain し、全対象 repo が clean であることを cutover gate にする。これは省略できない。

Lustre cross-node flock の最小実測:

1. repo 外の `/work/.../flock-probe/lock` を作る。
2. Job A が fd を開き `flock -n` 成功後、hostname と ready marker を書いて保持。
3. Job B は ready 後に異なる hostname であることを確認し、同 lock の `flock -n` が失敗することを記録。
4. login 側が release marker を書き、A 解放後に B の再試行が成功することを確認。
5. 同一 bnode に載った場合は不成立として再試行する。

この実測が失敗したら (b) 単独では 3 login node と caller crash を覆えないため NO-GO。atomic directory + lease 等は別設計として裁定へ返す。

### B3. walltime kill と復元

静的に確認できる範囲では、runbook は walltime directive と qdel しか規定しておらず、SIGTERM、SIGKILL 前 grace は書いていない。`_job_script()` に trap はなく、`_job_run()` は `subprocess.call()` で harness を待つだけである。`overall_grace=300` は login dispatcher の待機猶予であり、NQSV が child に与える signal grace ではない。

従って signal handler が間に合う前提には立たず、harness 自己 deadline を追加する。

- `_job_run()` が job 開始後に scheduler walltime から少なくとも 600 秒引いた monotonic deadline を内部 argv として注入する。
- caller はこの内部 flag を指定できない。
- collection、baseline、各 mutation の開始前に、次の timeout + restore reserve が残っているか確認する。
- 足りなければ新しい変異を適用せず、現在の ledger を flush、`_verify_originals()` と `_assert_head()` 後に rc=3。
- active mutation 中は既存 `_apply_mutation()` の `finally` 復元をそのまま維持する。
- resume は clean tree、同じ HEAD/spec/runner/tool の場合だけ行う。

予期しない SIGKILL 後の dirty tree を `--resume` が自動修復する変更は、この waveでは実装しない方がよい。自動修復には active-mutation journal と exact mutated/original byte 判定が必要で、誤った checkout を上書きする危険がある。dirty の場合は現行どおり fail-closed で停止し、DW-O19 の人手復元後に resume する。

NQSV signal の最小確認は、1 分 walltime の repo 外 probe jobで親・子それぞれに TERM/HUP/EXIT handlerを置き、walltime 到達時にどの PIDへ何秒前に signal が来るかを共有 FS へ fsync 記録する。結果が取れるまで「SIGTERM が来る」「grace がある」は未確認と記録する。

### B4. `--detached`

現行の `--detached` は manual background/tmux 起動との後方互換用に残す。scheduler job に意味を広げない。

新しい形:

- caller の mutation request では `--detached` を拒否。
- `_job_run()` が非公開 `--scheduler-job` と自己 deadline を注入。
- harness は scheduler mode のとき `PBS_JOBID`、bnode、`runner_mode=local` を確認。
- Pegasus login 上の実走 `runner_mode=dispatch` は拒否し、`dispatch_compute.py --task mutation` を案内。
- `--plan-only` は従来どおり実走 envelope 不要。

これなら検査を弱めず、フラグの意味も偽らない。

### B5. 証拠 field

`tools/mutation_harness.py:849-908` の per-run local artifact 契約は変更しない。

- collection、baseline、mutation 各 record は full inner stdout と `stdout_sha256` を持つ。
- `runner_mode=local` なので `receipt_path` / `job_stdout_path` は null のまま。
- 変異ごとの偽の receipt を作らない。

束ね一件の scheduler 証拠は、mutation ledger の外側に attempt 単位の transport ledger を置くのが最小である。

```json
{
  "schema": "izanagi-dev-wave-mutation-transport/v1",
  "request_id": "...",
  "repo_head": "...",
  "spec_sha256": "...",
  "mutation_out_path": "...",
  "ledger_before_sha256": null,
  "ledger_after_sha256": "...",
  "receipt_path": "...",
  "receipt_sha256": "...",
  "job_stdout_path": "...",
  "job_stdout_sha256": "...",
  "child_rc": 0
}
```

配置は `output/pegasus-dispatch/<nonce>/mutation-transport.json`。receipt には既知の manifest path を載せ、manifest は receipt、full job stdout、外部 ledger を hash で束縛する。manifest 永続化失敗時は child が 0 でも dispatcher rc=16 とする。

resume ごとに別 nonce・別 transport ledgerを作り、前回の `ledger_after_sha256` と次回の `ledger_before_sha256` で鎖にする。

この案では `LEDGER_SCHEMA` は v4 のままでよい。内側 ledger の exact-key validatorと local artifact契約を触らず、resume も同じである。内側 top-level に receipt field を追加するなら exact root key集合が変わるため v5 bump が必須だが、今回は勧めない。

なお harness の `tool_identity` は tool bytes exact一致を要求するため、今回のコード変更後は旧 toolで作った v4 ledgerをどのみち resumeできない。land前に旧走をdrainし、旧v4はread-only evidenceとして保存する。

### B6. テストと文書

新設・変更箇所:

| file:line | 変更内容 |
|---|---|
| `orchestrator/tests/test_pegasus_dispatch_compute.py:1397-1431` | exact task集合を3値へ更新。未知 task の親・CLI拒否は維持 |
| 同 `:1434-1487` 付近 | mutation の child script、4 env allowlist、3 imports、git probeを固定 |
| 同 `:1521-1579` | v1 tests互換を維持し、mutation child scriptをparametrizeへ追加 |
| 同 `:1379-1394` 付近 | childがallowlist外env、nested dispatch、不正repo/path、caller指定scheduler flagを拒否 |
| 同 `:1291-1376` 付近 | queue待ちがrunning walltimeを消費しないこと、N+2 walltime、86400超過拒否 |
| 同 receipt tests付近 | transport ledgerのreceipt/stdout/ledger hash、永続化失敗rc=16、resume hash chain |
| `orchestrator/tests/test_mutation_harness.py:365-386` | shared/legacy lockもrepo外であること |
| 同 `:698-704` |異なるnode-local temp rootを模擬してもshared lockが競合を拒否すること |
| 同 `:746-856` | signal復元を維持し、deadline不足時は次の変異を当てずclean rc=3、resumeで続行 |
| 同 resume tests `:409-579` | scheduler-local ledgerが同HEAD/spec/tool/commandでresumeできること |
| 同 artifact tests `:859-985` | local recordのreceipt/job pathが引き続きnull、stdout hashが再検証されること |

確実に変更が必要な既存テスト:

- `test_task_kind_enum_is_closed_and_unknown_task_is_setup_infra_rc` の exact集合 assertion。
- TASKSだけ先に変更すると `tools/check_docs.py` のrunbook inventory同期検査が失敗するため、runbook表と同一commitで更新する。
- `test_job_run_launches_task_specific_child_script` は直ちに落ちるとは限らないが、mutation caseを追加しなければ新契約を被覆しない。
- shared lock実装で `_lock_for()` の戻り値をcomposite holderにする場合、既存 `.close()` APIは保って `test_flock_rejects...` を不用意に壊さない。

文書:

- `docs/dev-wave/mutation.md:29-36`: bundled scheduler起動、shared lock、自己deadline、resume前cleanをDW-M05へ反映。
- `docs/pegasus-runbook.md:315-343`: D105 supersedeを反映し、task表へ `mutation` を追加。
- 同 `:514-529`: mutation起動、walltime、transport evidenceを追加。
- `tools/README.md:14-17`: sanctioned mutation taskを案内し、「追加にはD105 supersede」の記述を新Dへ更新。
- `docs/spool/decisions/`: D105(3) と D117(4) を supersedeする新D fragment。
- `tools/run_tests.py` と `site_policy.py` の実装変更は不要。

実装後に親が計算ノードで関連テスト、全走、`check_codex_agents.py`、`check_docs.py`、commit後provenance監査を行う。本回答ではいずれも実行しておらず、緑とは主張しない。

## C. 変異事前登録候補（DW-M01）

行は現ファイルの挿入 anchor。段4で統合後の実際の行と一意なold逐語へ再固定する。

| ID | file:line | old 逐語 | new 逐語 | 期待 status | 期待 failed node | 手前に同じ入力を拒否する検査がない根拠 |
|---|---|---|---|---|---|---|
| M01 | `tools/pegasus/dispatch_compute.py:55-73` | `child_script=("tools", "mutation_harness.py"),` | `child_script=("tools", "run_tests.py"),` | KILLED | `test_mutation_task_binds_child_script_environment_and_probe` | testがTASKS写像を直接読む |
| M02 | 同 `:475-481` 後 | `if unknown_environment:` | `if False and unknown_environment:` | KILLED | `test_job_run_rejects_mutation_environment_outside_allowlist` | `_job_run()`へ直接crafted requestを渡し親gateを迂回するfixture |
| M03 | 同 `:143-151` 後 | `if runner_mode != "local":` | `if False and runner_mode != "local":` | KILLED | `test_mutation_task_rejects_nested_dispatch` | task-specific validatorの最初のrunner-mode gate |
| M04 | 同 `:143-151` 後 | `run_count = len(spec.mutations) + 2` | `run_count = len(spec.mutations) + 1` | KILLED | `test_mutation_walltime_counts_collection_baseline_and_mutations` | pure estimatorを直接検査し、他のtime gateを通さない |
| M05 | 同 `:1180-1222` | `submitted_at + queue_wait_timeout_s + walltime_s + overall_grace_s` | `submitted_at + walltime_s + overall_grace_s` | KILLED | `test_queue_wait_does_not_consume_running_walltime` | fake clockでqueue待ちだけを進め、他timeout未到達にする |
| M06 | `tools/mutation_harness.py:1814-1835` | `return shared_root / f"izanagi-mutation-{key}.lock"` | `return Path(tempfile.gettempdir()) / f"izanagi-mutation-{key}.lock"` | KILLED | `test_shared_lock_rejects_competitor_across_distinct_temp_roots` |二つのlegacy tempを分け、shared lockだけを実効gateにする |
| M07 | 同 `:2048` 前 | `if remaining_s < timeout_s + RESTORE_RESERVE_S:` | `if False and remaining_s < timeout_s + RESTORE_RESERVE_S:` | KILLED | `test_scheduler_deadline_stops_before_applying_next_mutation_and_resumes` | clock fixtureでこの条件だけをdeadline境界にする |
| M08 | `tools/pegasus/dispatch_compute.py:1325-1360` 付近 | `"job_stdout_sha256": _file_sha256(stdout_path, "mutation job stdout"),` | `"job_stdout_sha256": "0" * 64,` | KILLED | `test_mutation_transport_manifest_binds_receipt_stdout_and_ledger` | manifest validatorが実stdout bytesと直接比較する |
| P01 | task argv validator、同 `:143-151` 後 | `if token == "--resume":` | `if False and token == "--resume":` | KILLED | `test_mutation_task_accepts_valid_fresh_and_resume_argv` | 他のrequired option、既存out、pathをすべて正しくした正例。新validationによる過剰拒否を検出する |

M02の親・子gateを別実装にする場合、単独変異は冗長gateでmaskされる。その場合はDW-M03に従い単独KILLから外し、両層同時変異として再登録する。

## D. 所有分割

編集集合を次のように完全分離する。

- 実装子A — dispatcher面

  - `tools/pegasus/dispatch_compute.py`
  - `orchestrator/tests/test_pegasus_dispatch_compute.py`
  - 必要な場合のみ `orchestrator/tests/test_check_docs.py`
  - 所有: TASKS、argv/env二層検査、walltime、deadline注入、transport ledger、legacy launcher lock

- 実装子B — harness面

  - `tools/mutation_harness.py`
  - `orchestrator/tests/test_mutation_harness.py`
  - 所有: shared/composite lock、scheduler envelope、自己deadline、N+2見積り、resume/復元契約

- 親 — docsと統合のみ

  - `docs/dev-wave/mutation.md`
  - `docs/pegasus-runbook.md`
  - `tools/README.md`
  - `docs/spool/decisions/<wave-fragment>.md`
  - 生死確認、実機flock/signal probe、全走、commit、記録

A/B間の固定interfaceは `runner_mode=local`、callerからscheduler flag禁止、`_job_run()`が内部deadlineを注入、外側transport ledgerはdispatcher所有、と段4で先に凍結する。両実装子にdocsや相手側testを編集させない。

## 総括

- 生死確認は N01/N03/N04 の3 node限定、同一HEAD/spec/SHA/test commandで現dispatchと一括local qsubを走らせ、4 verdict fieldを完全比較する。
- 最大のriskは、node-local lockと未確認のwalltime killが重なると変異済みtreeを残すこと。
- 親briefはD105 supersede要否、pytest中央値、`--resume`によるdirty回収、`--detached`の意味を誤っている。
- 現在は恒久実装NO-GO。verdict一致、cross-node flock成功、signal実測または自己deadline採用、旧process drain後にGO。
- 本回答は静的読解のみで、pytest・qsub・flock実測の成功を主張しない。