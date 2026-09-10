## 1. D131 の共通前提 6 点

**結論**

| # | 現在の充足状況 | 本 wave での扱い |
|---|---|---|
| 1 | 部分充足。wrapper の共有 lock はあるが、legacy harness lock は node-local のまま | mutation task の入口を wrapper に固定し、共有 artifact root を強制する変更まで本 wave 必須 |
| 2 | 現行の inner-dispatch 経路だけ充足。outer job + inner local へ替えると未充足へ戻る | 本 wave 必須 |
| 3 | 未充足 | 本 wave 必須 |
| 4 | 未充足 | 本 wave 必須 |
| 5 | 部分充足 | 本 wave 必須 |
| 6 | 完全充足 | 変更不要。既存回帰テストを再実行するだけ |

### #1 shared / legacy lock

**根拠**

- legacy harness lock は `tempfile.gettempdir()` 配下で、repo path の hash を鍵にする node-local lock である。`tools/mutation_harness.py:2863-2884`
- wrapper は `<--out>.lock` を `flock(LOCK_EX|LOCK_NB)` で保持し、同じ `--out` の二重 producer を拒否する。`tools/mutation_worktree.py:186-213`
- fanout は shard ごとに固有の ledger、wrapper receipt、evidence、lock を割り当てる。`tools/mutation_fanout.py:597-613`
- ただし group root は「registered worktree 外」しか検査せず、node-local path を明示的には拒否しない。`tools/mutation_fanout.py:363-377`
- D140 自身も「Lustre flock の実測は lock 移行窓を閉じない」と限定している。`docs/decisions.md:6878-6884`

したがって現在は「shared lock が存在する」までであり、D131 #1 全体は未充足である。

**変更**

- `tools/pegasus/dispatch_compute.py:99-135` の mutation task は必ず `tools/mutation_worktree.py` を起動し、harness 直接起動を許さない。
- mutation task の artifact root を `<--out>.dispatch-evidence` に固定し、`--out`、`--spec`、`--scratch-root`、wrapper lock が同じ外部 execution envelope に属することを親側と `_job_run` 側の両方で検査する。
- `tools/mutation_worktree.py:392-434` で、task 経路の artifact root が dispatcher request の置かれた root と一致することを検査する。compute job が request/script を読めなければ mutation 書込み前に失敗する。
- wrapper は共有 lock を保持したまま harness の legacy lockも取得する。既存 wrapper も同じ `<--out>.lock` を既に取るため、wrapper 経路では版移行時の無 lock 窓を作らない。
- direct harness 全般の node-local lock 廃止は別 task に切れる。ただし mutation task から direct harness を起動できないことが条件である。

### #2 永続 transport 証拠

**根拠**

- 現行 fanout は shard ごとに `.dispatch-evidence` を予約する。`tools/mutation_fanout.py:601-605`
- dispatch mode では disposable checkout 内の `output/pegasus-dispatch` を wrapper が外へ rename 退避する。`tools/mutation_worktree.py:683-699`
- wrapper receipt はその original/relocated path と状態を記録する。`tools/mutation_worktree.py:998-1026`
- attempt sidecar は各 inner invocation の request/receipt/stdout を記録する。`tools/mutation_harness.py:415-464`
- しかし local mode では `--attempt-out` 自体が拒否される。`tools/mutation_harness.py:2932-2941`、`tools/mutation_worktree.py:1126-1142`
- fanout merger も runner mode を `dispatch` に固定し、各 attempt の request object を必須にしている。`tools/mutation_fanout_contract.py:665-684`、`tools/mutation_fanout_contract.py:716-797`

したがって親 M6 の「#2 は充足済み」は、新しい outer-dispatch/inner-local 経路には成り立たない。

**変更**

- dispatcher の既存 split artifact root 機構を使う。`tools/pegasus/dispatch_compute.py:2407-2424`
- mutation task では outer dispatcher の request、receipt、job stdout/stderr を `<--out>.dispatch-evidence/<nonce>/` に直接永続化し、repo 内の gitignore rootだけに残さない。
- local modeでも attempt sidecarを許可する。各 collection/baseline/mutation entry の `request` は `null` とし、inner qsub が無かったことを表す。
- outer receipt の `request.args` に `--out`、`--attempt-out`、`--wrapper-attempt` が exact に残るため、次の鎖を merger で検証する。

```text
outer receipt
  -> wrapper argv / wrapper attempt
  -> wrapper receipt
  -> local attempt sidecar
  -> ledger の collection / baseline / mutation 行
```

- `tools/mutation_fanout_contract.py:60-75` の group/expected-path 契約へ outer transport artifact root を追加する。
- `tools/mutation_fanout_contract.py:1269-1405` は、local ledger の各行に inner receipt を要求せず、shard または wrapper invocation ごとの outer receipt 1 件を検証する形へ分ける。
- request 総数の期待値も inner-dispatch の `変異数 + 2N + history` から outer wrapper invocation 数へ変更する。現在の式は `tools/mutation_fanout_contract.py:1470-1474`。

### #3 login node での local 直起動

**根拠**

- harness parser は `local` と `dispatch` を無条件に受理する。`tools/mutation_harness.py:2906-2928`
- local mode の subprocess 起動前に site 判定はない。`tools/mutation_harness.py:1822-1880`
- worktree wrapper も同様に両 mode を無条件に受理する。`tools/mutation_worktree.py:1108-1123`
- よって現状は未充足である。

**変更**

- `tools/mutation_harness.py:2932-2985` で、repo 解決後かつ lock/collection 前に `site_policy.current_site()` を呼ぶ。
- `PEGASUS_LOGIN` と `PEGASUS_SUSPECT` の `--runner-mode local` を rc=2 で拒否する。`OTHER` と `PEGASUS_COMPUTE` は維持する。
- `tools/mutation_worktree.py:1126-1152` にも同じ拒否を置き、disposable worktree 作成前に止める。
- site 判定は `orchestrator/campaign/site_policy.py:30-46,66-97` を直接再利用し、hostname 判定を手で写さない。

### #4 canonical 全走 argv

**根拠**

- 現在の harness は `-rf` を要求するだけで、`-p no:cacheprovider` は無ければ後付けする。`tools/mutation_harness.py:2942-2953`
- `_assert_tracked_test_arguments` は target が tracked かを検査するだけで、`-k`、`-m`、nodeid、任意 `-p` を許している。`tools/mutation_harness.py:868-907`
- collection も元 command の選択・設定引数を温存する。`tools/mutation_harness.py:1366-1397`

よって canonical 全走の固定にはなっていない。

**変更**

- `_TaskSpec` に literal な `argv_policy="mutation-worktree-v1"` を追加し、親側 `_dispatch_impl` と子側 `_job_run` の双方で同じ validator を呼ぶ。
- task 経路の runner tail は次の exact 形だけを受理する。

```text
<同一 Python> tools/run_tests.py -rf -p no:cacheprovider
```

- positional target、`::nodeid`、`-k`、`-m`、`--deselect`、`--ignore*`、追加 `-p`、`PYTEST_ADDOPTS`、`PYTEST_PLUGINS`、`--force-dispatch` を拒否する。
- 既存の targeted mutation harness 利用は task 外では維持する。canonical 制約を harness 全利用へ一律適用すると、既存 targeted matrix の受理集合を不必要に壊す。

### #5 env / stdin / cwd / rc

**根拠**

- `_job_run` は `os.environ.copy()` に request env を無条件で混ぜる。`tools/pegasus/dispatch_compute.py:696-715`
- dispatcher から child への `subprocess.call` は cwd を repo root に固定するが、stdin を閉じていない。`tools/pegasus/dispatch_compute.py:719-724`
- wrapper から harness は stdin を閉じ、cwd を container に固定している。`tools/mutation_worktree.py:795-808`
- harness から runner も stdin を閉じ、cwd を実 checkout に固定している。`tools/mutation_harness.py:1871-1880`
- harness は pytest/Python injection env を除去する。`tools/mutation_harness.py:1833-1847`

したがって cwd は充足、stdin は最外層だけ未充足、env は部分充足、rc の outer transport 対応は未確定である。

**変更**

- mutation task に `env_mode="clean"` を指定し、dispatcher 内の共通 child-env builderで `PATH`、`HOME`、locale、`USER`/`LOGNAME`、`TZ`だけを基礎環境として作る。`PYTHONDONTWRITEBYTECODE=1` は dispatcher が設定する。
- `PYTEST_*`、`PYTHON*`、`GIT_*`、`LD_*`、proxy、任意 `IZANAGI_*` は task request から受け取らない。task 固有値は argv で渡す。
- `tools/pegasus/dispatch_compute.py:720-724` の child call に `stdin=subprocess.DEVNULL` を追加する。
- artifact は外部 artifact root の同一 envelope 内に限定し、親と子で二重検査する。
- rc の意味は第4節の表で固定する。

### #6 deadline / qdel

**根拠**

- pre-RUN deadline は submission 時刻から設定される。`tools/pegasus/dispatch_compute.py:2941-2945`
- rc=0 の RUN 初観測で `walltime + grace` へ一度だけ張り直される。`tools/pegasus/dispatch_compute.py:2987-2997`
- qdel gate は target-bound state が `QUE` または `HLD` の場合だけ許可する。RUN、END、UNKNOWN は拒否する。`tools/pegasus/dispatch_compute.py:1979-2001`
- RUN timeout の既存回帰テストも qdel 非起動を検査している。`orchestrator/tests/test_pegasus_dispatch_compute.py:3712-3740`
- canonical decision も両方を閉じたと記録する。`docs/decisions.md:6988-6994`

**変更**

- production 変更なし。
- deadline rebase と fresh-qstat gate の既存テストを親が再実行する。未実走を緑とは記録しない。

## 2. mutation task の `_TaskSpec`

**結論**

具体形は次である。

```python
"mutation": _TaskSpec(
    child_script=("tools", "mutation_worktree.py"),
    env_allowlist=frozenset(),
    probe_imports=("pytest", "xdist", "packaging"),
    env_mode="clean",
    argv_policy="mutation-worktree-v1",
),
```

`child_script` は `mutation_worktree.py` であり、`mutation_harness.py` でも `mutation_fanout.py` でもない。

束ねる単位を task 自体の契約として「shard」と固定する P2 は過剰である。正しい単位は「1 wrapper invocation = 1 job」である。fanout callerでは wrapper invocation が shard と一致するが、full parent spec を渡す非 fanout 呼出しでは全 spec が1 jobになる。

**根拠**

- `mutation_worktree.py` が disposable checkout、共有木前後観測、shared output lock、teardown、wrapper receipt を所有する。`tools/mutation_worktree.py:79-120`、`tools/mutation_worktree.py:937-1026`
- harness 直接起動では wrapper receipt と disposable checkout の外部復旧境界がない。`tools/mutation_harness.py:2932-3196`
- fanout は shard ごとに wrapper argv を1本生成する。`tools/mutation_fanout.py:590-688`
- shard 分割は親 spec から決定的に再導出される。`tools/mutation_fanout_contract.py:506-591`
- fanout 自体は login coordinatorであり、複数 wrapper の起動、merge、cancel を所有する。`tools/mutation_fanout.py:1424-1781`
- `mutation_fanout.py` を task child にすると group全体が1 PBS jobになり、既存の「shardごとの wrapper receipt / rc / cleanup」境界と一致しない。
- `pytest` distribution identity は harness が必須にする。`tools/mutation_harness.py:837-865`
- `run_tests.py` は import 時に `packaging` を使い、computeでは pytest-xdist を必須にする。`tools/run_tests.py:49-54`、`tools/run_tests.py:2640-2656`
- task固有の runtime pathはすべて argv にあり、worktree側が `GIT_TERMINAL_PROMPT=0` を自分で設定するため、request env allowlist は空でよい。`tools/mutation_worktree.py:132-154`、`tools/mutation_worktree.py:702-739`

P2については、既存 fanoutをそのまま新 transportへ結ぶなら「shard 1本 = wrapper 1本 = job 1本」が自然である。ただし次の2点から、無条件の既定にはできない。

- D130/D842 の一次文言は「harnessを1 jobへ束ねる」であり、shard化を明示していない。`docs/decisions.md:6324-6336`、`docs/decisions.md:31747-31757`
- 現行 fanout admission は `memory.peak` 不在により実機では常に拒否されると確定している。`tools/mutation_fanout.py:401-418`、`docs/decisions.md:18009-18023`

**変更**

- `tools/pegasus/dispatch_compute.py:99-135` に上記 literal entry を追加する。
- `tools/pegasus/dispatch_compute.py:2398-2401` と `:688-704` の両方で `argv_policy` を検査する。
- `tools/mutation_worktree.py:1108-1148` は task 経路の local mode、canonical runner、outer artifact root binding を検査する。
- `tools/mutation_harness.py:2932-2955` は local attempt sidecarと site gateを受理するよう変更する。
- fanout連携を選ぶ場合だけ、`tools/mutation_fanout.py:656-688` が生成する wrapperを `task="mutation"` の outer dispatcherで包む。現行 admissionを黙って迂回してはならず、D433の扱いを段4で先に裁定する。

## 3. 計算ノード内で local 実行になる経路

**結論**

outer job が成立すれば、内側 `run_tests.py` は現行コードだけで local 実行になる。止める主体は `PBS_JOBID` ではなく、権威ある bnode hostname を使う `site_policy.current_site()` と `run_tests.py` の compute 分岐である。

ただし login node から harness local を直接起動する抜け道は現状止まらないため、site gate と canonical argv拒否を追加する。

**根拠**

```text
login mutation caller
  -> dispatch_compute task=mutation
  -> compute _job_run
  -> mutation_worktree.py --runner-mode local
  -> mutation_harness.py --runner-mode local
  -> tools/run_tests.py
  -> pytest subprocess
```

- job script は bnode hostname でなければ child 起動前に rc=16。`tools/pegasus/dispatch_compute.py:602-605`
- `_job_run` も独立に bnode hostname を要求する。`tools/pegasus/dispatch_compute.py:705-707`
- `site_policy` は bnodeを `PEGASUS_COMPUTE` に分類する。`orchestrator/campaign/site_policy.py:30-46`
- `run_tests.py` の dispatch 分岐は login node 内にしかない。`tools/run_tests.py:2620-2637`
- computeでは xdistを検査した後、pytest commandを直接起動する。`tools/run_tests.py:2640-2656,2682-2708`
- `--force-dispatch` が残っていても computeでは login分岐へ入らないが、canonical argvからは拒否して二重防壁にする。

**変更**

- fanoutまたは直接 callerが生成する wrapper argsを `--runner-mode local` にする。
- task argv policyで `--force-dispatch` を拒否する。
- `tools/mutation_harness.py:2932-2985` と `tools/mutation_worktree.py:1126-1152` に login/suspect local拒否を追加する。
- `_job_script`、interpreter probe、PATH先頭化はそのまま使う。`tools/pegasus/dispatch_compute.py:524-547,556-633`
- 環境正規化を fanout/worktreeへ再実装しない。

## 4. D117 決定4の (b)(c)(d)

**結論**

(b) は全task共通で直す。(c)(d) は mutation profile と外部証拠契約で固定する。既存 `tests` / `provenance` の正規親経路は壊れない。

### (b) env allowlist の全キー強制

**根拠**

- 現在は request env の型だけを検査し、そのまま混ぜる。`tools/pegasus/dispatch_compute.py:697-710`
- allowlistを子側で使うのは task-run marker 2名の除去だけである。`tools/pegasus/dispatch_compute.py:711-715`
- 親側は task allowlistから request envを構成する。`tools/pegasus/dispatch_compute.py:2487-2491`
- `tests` の正規 request は allowlist内だけになる。既存テストもその exact集合を固定している。`orchestrator/tests/test_pegasus_dispatch_compute.py:4001-4010`
- `provenance` は空環境を生成する。`orchestrator/tests/test_pegasus_dispatch_compute.py:4084-4117`
- v1互換テストの `PYTEST_ADDOPTS` も tests allowlist内である。`orchestrator/tests/test_pegasus_dispatch_compute.py:4202-4229`

**変更**

`tools/pegasus/dispatch_compute.py:697-710` に次を追加し、`child_env.update` より前に拒否する。

```python
unexpected = set(requested_env) - spec.env_allowlist
if unexpected:
    raise DispatchError("environment に task allowlist 外 key がある")
```

これにより壊れるのは forged requestだけで、現行の正規 `tests`、`provenance`、v1 requestは通る。

### (c) stdin / cwd / artifact visibility

**根拠**

- dispatcher child cwd は repo root。`tools/pegasus/dispatch_compute.py:708-724`
- wrapper/harnessのcwdは container/checkoutに固定済み。`tools/mutation_worktree.py:795-808`、`tools/mutation_harness.py:1871-1880`
- dispatcher最外層だけstdin未閉鎖。
- dispatcherにはrepo外 artifact rootとrepo内共有control rootを分ける既存機構がある。`tools/pegasus/dispatch_compute.py:2407-2424`

**変更**

- dispatcher child stdinを `DEVNULL` にする。
- mutation artifact rootを外部 `<--out>.dispatch-evidence` に固定する。
- spec、scratch、ledger、attempt、wrapper receipt、lockを同じ execution envelopeへ束縛する。
- compute marker、result、receipt、scheduler stdoutが同じ rootへ書けたことをartifact visibilityの実証とする。単なる path字句の検査だけで「見える」と主張しない。

### (d) 子 rc

**根拠**

| 層 | rc | 意味 |
|---|---:|---|
| mutation harness | 0 | 全recordが期待statusと一致 |
| mutation harness | 1 | 完走したが期待status不一致あり |
| mutation harness | 2 | harness fail-closed、orphan stop、parse/contract停止 |
| mutation harness | 128+signal | signal abort |
| worktree wrapper | 0 / 1 / 2 | harness rcの伝播 |
| worktree wrapper | 125 | wrapper/preflight/teardown/receipt失敗 |
| worktree wrapper | 128+signal | signal abort |
| compute dispatcher | 16 | scheduler、receipt、accounting等のtransport infra失敗 |

- harnessの0/1選択は `tools/mutation_harness.py:3171-3183`。
- harness error/signalのrcは `tools/mutation_harness.py:3199-3218`。
- wrapper rc選択は `tools/mutation_worktree.py:988-995,1358-1368`。
- dispatcher infra rcは `tools/pegasus/dispatch_compute.py:40-61`。
- verified child rcはそのまま返る。`tools/pegasus/dispatch_compute.py:3132-3186`

dispatcherの `INFRA_RC=16` と harness/worktreeの0、1、2、125は衝突しない。

ただし `tools/mutation_fanout.py` 自身も `INFRA_RC=2` を使う。`tools/mutation_fanout.py:54-55`。これは harness rc=2 と数値衝突する。fanout連携時はraw rcだけで分類せず、outer dispatcher receiptの `outcome.kind`、wrapper receipt、driver reportに `transport_kind` と `child_rc` を別欄で残す必要がある。

**変更**

- dispatcher rc体系は変更しない。
- mutation receipt consumerは `outcome.kind=="child"` と `accounting_verified is True` を要求する。
- fanout reportは shardの `process rc`、dispatcher `outcome.kind`、wrapper `child_rc` を別欄にする。rc=2を一語の「infra」に畳まない。

## 5. 汎用 task と P1

**結論**

P1の安全方向は正しい。ただし「投入表を拡張可能にする」ことは、ユーザーが述べた「任意コマンドを送る汎用 task」の実装ではない。ここを同一視して完了扱いにしてはならない。

安全に作れるのは、固定 `child_script`、固定env、固定probe、固定argv policyを持つ profileを `TASKS` に追加する方式だけである。callerが任意 executable/argvを渡す真の generic taskは、D103を維持したままでは安全に作れない。

**根拠**

- hookでは `dispatch_compute.py` が `local-ok` として登録されている。`tools/pegasus/admission_registry.json:34-38`
- registryの `local-ok` pathは sanctioned集合へ入る。`hooks/guard_bash.py:280-294`
- sanctioned scriptは重量command判定の途中で早期許可される。`hooks/guard_bash.py:1226-1230`
- その後ろにある直接pytest/build/perf拒否には到達しない。`hooks/guard_bash.py:1232-1268`
- hookのparserは dispatcherの `--` 後を新しいshell commandとして再帰解析しない。`hooks/guard_bash.py:962-1000`
- したがって、dispatcherが任意commandをexecできるようになると、次の形はhookを通過する。

```text
python3 tools/pegasus/dispatch_compute.py --task generic -- python3 -m pytest ...
```

- D103が守る性質は「hookのsanctioned pathはexactであり、任意exec trampolineをsanctionしない」である。`docs/decisions.md:4599-4606`
- D105も任意command化を明示的に拒否した。`docs/decisions.md:4710-4714`

**変更**

安全な一般化としては次だけを行う。

- `tools/pegasus/dispatch_compute.py:99-105` の `_TaskSpec` に `env_mode` と `argv_policy` を足す。
- task追加時は literal `child_script` と closed policyを必須にし、親と子の二層で検査する。
- `TASKS` はliteral定義のままとし、runtime registry、path引数、shell文字列、`os.exec*` trampolineを入れない。
- `generic` / `shell` / `command` taskは追加しない。

段4で親が裁定へ返すべき択一は次である。

1. D842の「汎用 taskを扱う」を、上記profile方式の設計確定と「任意command taskは作らない」という結論で満たす。
2. caller任意commandを本当に要求するなら、D103決定5を明示的にsupersedeし、hookでは守れない新しい信頼境界をユーザーが受理する。

後者を裁定なしに実装する安全設計はない。

## 6. `check_docs.py` の drift 検査

**結論**

`tools/check_docs.py` のproduction AST抽出ロジックは変更不要である。既に任意個数のliteral `_TaskSpec(child_script=(...))` を抽出する。必要なのは `TASKS` をliteralのまま増やすこと、runbook表へ同じ行を足すこと、テストの期待写像を更新することである。

**根拠**

- AST parserはliteral `TASKS` dictを要求する。`tools/check_docs.py:3289-3337`
- 定義後の再束縛、alias、mutationを拒否する。`tools/check_docs.py:3339-3449`
- 各entryのliteral `child_script` を一般的に抽出する。`tools/check_docs.py:3451-3492`
- runbook表と `{task: child_script}` でexact比較する。`tools/check_docs.py:3515-3553`
- exact表は現在2行だけである。`docs/pegasus-runbook.md:588-593`

**変更**

- `tools/pegasus/dispatch_compute.py:110-135` のliteral `TASKS`へ mutation entryを追加する。
- `docs/pegasus-runbook.md:565-574` の「2 taskだけ」「第3 task未実装」をD842後の状態へ更新する。
- `docs/pegasus-runbook.md:588-592` に次を追加する。

```markdown
| `mutation` | `tools/mutation_worktree.py` |
```

- `orchestrator/tests/test_check_docs.py:2585-2593` のreal dispatcher期待写像へ mutationを追加する。
- synthetic parser fixtureは2行のままでも一般抽出を検査できるため、production `check_docs.py` にmutation固有分岐を足さない。
- `docs/decisions.md` のD105本文は履歴として改竄せず、D842とrunbookの現行説明でsupersedeを表す。

## 7. テスト計画

**結論**

次のfocused testを追加または変更する。すべて、条件を反転・削除したときに観測可能な赤になる形にする。

### `orchestrator/tests/test_pegasus_dispatch_compute.py`

- `test_task_kind_enum_is_closed_and_unknown_task_is_setup_infra_rc` を変更し、exact集合を `{tests, provenance, mutation}` にする。  
  検査がないと、task追加漏れまたは未知taskのscheduler到達が静かに通る。

- `test_mutation_task_binds_worktree_clean_env_and_probe_imports` を追加する。  
  検査がないと、childをharness/fanoutへ誤配線したり、computeでpytest/xdist不足のままworktreeを書き始める。

- `test_job_run_rejects_every_allowlist_external_environment_key_before_child` を追加する。  
  検査がないと、forged requestが `PYTEST_PLUGINS`、`PYTHONPATH`、任意envをchildへ注入できる。

- `test_valid_tests_v1_v2_and_provenance_requests_survive_child_env_enforcement` を追加する。  
  検査がないと、fail-closed強化が正規の既存2経路やin-flight v1を過剰拒否しても気付けない。

- `test_mutation_argv_policy_rejects_selector_nodeid_plugin_and_force_dispatch_before_qsub` を追加する。  
  検査がないと、「canonical全走」の名前の下でsubsetや任意pluginを実行できる。

- `test_mutation_job_run_closes_stdin_and_uses_repo_cwd` を追加する。  
  検査がないと、TTY入力待ちまたはcaller cwd依存が再発する。

- `test_mutation_split_artifact_root_persists_outer_receipt_and_stdout` を追加する。  
  検査がないと、receiptがgitignore下だけに残り、ledgerからtransport証拠が切れる。

- `test_mutation_child_rc_and_dispatch_infra_rc_are_distinct` を追加する。  
  検査がないと、child rc=1/2/125をdispatch infra=16として誤分類する。

既存の以下は変更せず再実行する。

- `test_queue_wait_does_not_consume_observed_run_budget`
- `test_overall_walltime_plus_grace_bound_skips_qdel_for_fresh_running_job`
- `test_trusted_run_after_nonzero_run_stdout_restarts_deadline`

### `orchestrator/tests/test_mutation_harness.py`

- `test_login_local_mode_refuses_before_collection_lock_or_ledger` を追加する。  
  検査がないと、login nodeでlocal full runを直接起動できる。

- `test_compute_and_other_local_mode_remain_admitted` を追加する。  
  検査がないと、login拒否を全site拒否へ誤実装して既存非Pegasus利用を壊す。

- `test_local_attempt_sidecar_records_null_inner_request_and_wrapper_ordinal` を追加する。  
  検査がないと、outer receiptとledger各行のattempt対応が失われる。

- `test_transport_local_runner_is_exact_full_suite` を追加する。  
  検査がないと、harness側の既存の緩いargument検査だけでtask validatorの欠落が隠れる。

### `orchestrator/tests/test_mutation_worktree.py`

- `test_same_out_from_different_scratch_is_rejected_between_observation_points` を維持し、task artifact root下でも同じshared lockが競合するcaseを追加する。  
  検査がないと、同一wrapper attemptが別nodeで二重走行する。

- `test_outer_transport_root_is_bound_to_out_and_wrapper_receipt` を追加する。  
  検査がないと、別runのreceiptをwrapper ledgerへ付け替えられる。

- `test_local_wrapper_tears_down_without_requiring_inner_dispatch_evidence` を追加する。  
  検査がないと、inner local化後も存在しないinner receiptを要求して正常runを125へ落とす。

- `test_child_return_code_is_propagated_between_observation_points` を2、125を含むcaseへ拡張する。  
  検査がないと、harness停止とwrapper失敗が同じraw rcへ潰れる。

### `orchestrator/tests/test_mutation_fanout.py` と `test_mutation_fanout_contract.py`

fanout連携を段4で採る場合だけ追加する。

- `test_one_outer_mutation_dispatch_per_shard_and_no_inner_dispatch`。  
  検査がないと、1 mutation = 1 qsubの旧経路が残るか、全shardが1jobへ誤結合される。

- `test_outer_dispatch_infra_stops_group_without_retry_or_merge`。  
  検査がないと、部分成功だけをmergeして欠落shardを完成扱いにする。

- `test_merge_accepts_local_ledger_with_one_transport_receipt_per_wrapper_attempt`。  
  検査がないと、新旧証拠モデルのどちらも実際には受理できない恒偽gateになる。

- `test_merge_rejects_transport_task_args_rc_stdout_and_wrapper_binding_mutations`。  
  検査がないと、別task、別argv、別stdout、別wrapperのreceipt差替えが静かに通る。

- `test_transport_request_count_is_wrapper_count_not_inner_invocation_count`。  
  検査がないと、旧 `変異数 + 2N` 算式が残り、outer束ねが正しくても必ず拒否される。

### `orchestrator/tests/test_hooks.py`

- `test_dispatch_gateway_is_sanctioned_before_inner_argv_heavy_scan` を追加し、現行hookがdispatcherの内側を検査しないことをpositive controlとして固定する。  
  検査がないと、「hookがgeneric taskの任意argvを止める」という誤った安全主張が再発する。

- task表に任意exec trampolineが入っていないことは dispatcher testで固定し、hookにargv parserを後付けしない。

### `orchestrator/tests/test_check_docs.py`

- `test_dispatch_inventory_accepts_real_dispatcher_tasks_reads` の期待写像へmutationを追加する。  
  検査がないと、production表とAST抽出の更新漏れが見えない。

- `test_dispatch_inventory_deleted_mutation_row_is_rejected` を追加する。  
  検査がないと、新規行だけrunbookから消えても既存2行の正例で検査が緑に見える。

本回答ではテストを実走していない。静的計画であり、緑の主張はしない。

## 総括

### (a) 実装順序

1. 段4で「wrapper invocation単位」とfanout連携の扱い、汎用taskの意味を裁定する。
2. `dispatch_compute.py` に `_TaskSpec` のenv/argv policyとmutation literal entryを追加する。
3. 全key env強制、stdin閉鎖、外部artifact root、outer receipt永続化を実装する。
4. `mutation_worktree.py` と `mutation_harness.py` にlocal site gate、local attempt sidecar、outer evidence bindingを入れる。
5. fanoutを採る場合だけ `mutation_fanout.py` と `mutation_fanout_contract.py` をouter-receiptモデルへ移行する。
6. runbook exact表と `test_check_docs.py` の期待写像を更新する。
7. 親がfocused tests、`check_codex_agents.py`、`check_docs.py`、受入全走を実測する。

### (b) 親が段4で裁定すべき論点

1. P2を「taskの単位はshard」とするか、「taskはwrapper invocation単位で、shard化はcaller責務」とするか。推奨は後者。
2. 現行fanoutはD433により実機で恒偽である。T-360にfanout admission再設計まで含めるか。
3. D842の「汎用taskを扱う」を、closed profile方式と任意command不採用の結論で満たすか。真の任意commandを要求するならD103の明示supersedeが必要。
4. P4は、変更をdev harness、task集合、development ledger schemaに限定する限り正しい。certified選択、proof chain、既存freezeを動かしてはならない。

### (c) 本 wave の scope 外へ出すべきもの

- mutation taskを経由しないdirect harness全般のlegacy node-local lock廃止。
- P2を採らない場合の `mutation_fanout.py` admission schema v2化とD433の再裁定。
- hookが任意script内部まで解析する仕組み。現行hookの信頼境界を越える。
- frozen研究成果物、certified選択、campaign受理集合の変更。
