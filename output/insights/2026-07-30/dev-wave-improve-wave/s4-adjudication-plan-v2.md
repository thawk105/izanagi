# 段4裁定 — Pegasus compute dispatch plan v2

## 結論

段2 plan はそのまま採用しない。今回の wave は、ユーザーの直接要件である
「Pegasus login node で build / pytest を実行しない」を standard entrypoint で機械執行し、
この wave 自身の build・test・mutation・受入も compute node で行う。

build 並列度を affinity 全数へ変える案と official floor の build provenance v3 は、
既存 cache / ratified 受理集合を変えるため同時実装しない。build は今回も既定 `-j16` を維持し、
実行場所だけ compute に限定する。pytest は既存の explicit override を尊重し、default は
compute affinity 全数とする。

保証は repository の standard runner、buildcache miss、指定 direct-build helper、
Claude Bash の既知 command 形に限定する。Codex、任意 shell、alias、encoded command、
管理者権限外 surface を覆う system-wide security boundary とは記述しない。

## 段3所見の裁定

| 所見 | real / refuted | 採否 | scope | 放置時の成果物影響 |
|---|---|---|---|---|
| unknown NQSV / Pegasus-like hostname が OTHER へ落ちる | real | 採用 | 今回 | login/compute の誤分類で local pytest/build receipt が正規化される |
| qlogin の PBS identity 未実測 | real | fail-closed のみ採用 | qlogin自動受理は外 | allocation を local 扱いするか正規 qlogin を過剰拒否する |
| `campaign.pegasus_policy` import identity | real | 配置案を棄却 | 今回 | runner/hook/campaign が別型または import error になる |
| absolute target が元worktreeを指す | real | 採用 | 今回 | snapshot hashと実行test bytesが不一致になる |
| staged/unstaged index drift | real | 採用 | 今回 | deletion/preflightの受理結果が投入元と変わる |
| adversarial ABAでも瞬間snapshotを保証 | real | 保証を縮小 | 外 | 複数fileが実在しなかった組合せになりうる |
| pytest no-executionがplugin/fixture codeをloginで動かす | real | 採用 | 今回 | login code executionがreceiptなしで起きる |
| qsub後の親死亡・ID不明に復旧手段なし | real | 採用 | 今回 | orphan/二重job/task-run重複が残る |
| qstat pending/running/disappearanceを一状態で扱う | real | 採用 | 今回 | 正規job取消または不完全jobを成功扱いする |
| compute Python/packageを一probeから一般化 | real | 採用 | 今回 | 別allocationの欠落/skip driftを偽比較する |
| guardが全surfaceを強制できる | real | 表現を限定 | 今回 | hook外のlogin loadを「不可能」と誤報する |
| named build routesで全repository buildを覆う | real | 保証を限定 | 外 | t152等のdirect buildがloginで残る |
| v2 fresh actual argvとreturned argvが不一致 | real | 現fieldはreproductionと裁定 | v3は外 | actual historyとreproductionを同名fieldで混同する |
| official floorをfresh-onlyにする | realな破壊案 | 棄却 | 外 | pilot→official、retry、resumeのvalid hitをpoison化する |
| `cached` をratifiabilityへ昇格 | realな破壊案 | 棄却 | 外 | invocation-local stateでofficial受理集合を縮小する |
| buildcache/v3 producer receipt | realな必要性 | 設計パッケージ | 外 | future official argv/jobsに独立proof edgeがない |
| login cache hitまで拒否 | realな過剰拒否 | 棄却 | 今回 | CPUを使わないvalid read-only cache利用を失う |
| existing 23 freeze / active不在 / no reissue | refutedなし | 維持 | 今回 | 不要な凍結bytes更新が起きる |
| 48 workerが常に速い | refuted | 主張しない | 今回 | 単発差0.88%を性能一般化してしまう |

## gate適用

- G01: probe `874129.nqsv` で bnode114、affinity 48、Python 3.10.12、
  pytest全走の生死を確認済み。
- G02: 初回cycle前blockerは login execution、source-byte不一致、scheduler result誤認、
  task-run二重記録に限定する。v3 official proof-chainはfuture発行条件であり今回のblockerにしない。
- G03: runner / buildcache / direct coverage の独立entrypointで同型のsite欠落を確認したため、
  stdlib-only site policyの共有は成立する。ただしsystem-wide enforcementへ一般化しない。
- G04: qloginのPBS fieldとactive official v3 artifact pathを書けないため、qlogin自動受理と
  v3 ratificationは実装せずfail-closed / design packageに留める。
- G05: 各採用所見の成果物影響は上表に記録した。

## plan v2

### U1 — canonical site policy

所有:

- `tools/pegasus_policy.py`（新規）
- `orchestrator/tests/test_pegasus_policy.py`（新規）

単一 canonical import名を `pegasus_policy` とし、runner、hook、campaign、submitterは
`__file__` 由来の `<repo>/tools` を import 前に挿入する。`campaign.*` と
`orchestrator.campaign.*` の二重型を作らない。

policyはstdlib-onlyで、raw/canonical hostname、raw/normalized PBS ID、affinity、
`PEGASUS_LOGIN / PEGASUS_COMPUTE / OTHER` を返す。

- canonicalize: ASCII lowercase、末尾dot一個除去。
- known login: `pegasus01/02/03` とexact FQDN。PBS IDがあれば拒否。
- known compute: `bnode[0-9]{3}` とexact FQDN。NQSV PBS IDと非空affinity必須。
- unknown hostname + NQSV、Pegasus domain未知host、`pegasus*` / `bnode*` 類似名は拒否。
- その他はOTHER。
- qloginらしいbnode + PBS欠落は、実測がないので拒否。
- compute default pytest workersはaffinity全数。otherは現行cap32。
- explicit `-n0` はserialとして維持し、正整数がaffinityを超える場合は拒否。
- build jobsは今回解決しない。現行 `-j16` を維持する。

### U2 — test snapshot / synchronous PBS dispatcher

所有:

- `tools/run_tests.py`
- `tools/pegasus/test_dispatch.py`（新規）
- `tools/pegasus/submit_tests.py`（新規）
- `tools/pegasus/run_tests_job.sh`（新規）
- `orchestrator/tests/test_pegasus_test_dispatch.py`（新規）
- `orchestrator/tests/test_run_tests_nproc.py`
- `orchestrator/tests/test_run_tests_preflight.py`
- `orchestrator/tests/test_run_tests_task_run.py`
- `orchestrator/tests/test_pegasus_tools.py`
- `.gitignore`

local-only形は wrapper自身が処理する exact `run_tests.py --help` / `--version` だけとする。
pytestを起動するhelp/collect/setup形はcomputeへ送る。`packaging`はxdist branchまでlazy importする。

login executing形はpreflight/task-run/xdistより前にdispatcherへ渡す。compute側は
hash-bound authorization markerとPBS identity一致時だけlocal runnerへ進み、
preflight、xdist検査、pytest、task-run attemptを一回だけ実行する。computeではpip/networkを
使わず、Python>=3.10とpytest/xdistが同interpreterに無ければinfra failureにする。

snapshot:

1. qstat-Q / pegasusinfo / budget / quota を先に検査する。
2. dispatch rootはsource tree外のcreate-only sibling namespace。
3. local cloneはsystem/global config、hooks、filters、remote、alternatesを無効化する。
4. detached HEADへcached patchを`git apply --index`、unstaged patchをworktree-onlyで適用する。
5. nonignored untrackedと明示許可したignored fixtureをpath/mode/link-target/SHAで固定する。
6. submodule gitlink、HEAD、cached/unstaged/untrackedを同じ規律で固定する。
7. repo内absolute argvはsnapshot-relative表現へ変換し、workerでsnapshot rootへ解決する。
   外部target、argsfile、plugin/path注入、symlink escapeはhash-bound stagingできなければ拒否する。
8. source/snapshotのstatus-v2、diff、inventoryを比較し、通常の並行変更を検出する。
   adversarial瞬間snapshotは主張しない。

scheduler:

- qsub前にappend-only fsync済みdispatch journalとpre-submit authorizationを作る。
- dispatch_idをjob name、env、receipt pathへ束縛する。
- visibility grace、queued/held、pre-running、running、terminal/disappeared、
  log grace、accountingを別状態・別timeoutで扱う。
- raw qsub ID、worker PBS ID、normalized IDを分離する。
- qstat一時失敗をterminalと見なさず、各pollのraw/rcを保存する。
- stdout/stderrはfile spoolし、receiptはpath/size/SHAのみ。replayはstreaming上限付き。
- child rcはhash-bound runner-resultがある場合だけ採用する。
- cancel intentは一回、qdel attemptはbounded retry。遅着successへ反転しない。
- `resume --dispatch-id` を持ち、SUBMIT_UNKNOWNを自動再qsubしない。
- task-runは観測eventでありdispatch成功の正本にしない。attempt一回とevent有無をreceiptへ残す。

### U3 — login-node build miss gate

所有:

- `orchestrator/campaign/buildcache.py`
- `orchestrator/campaign/s2_verify_calibration.py`
- `orchestrator/campaign/s3_lock_coverage.py`
- `orchestrator/campaign/s5_permutation_coverage.py`
- `orchestrator/campaign/s8a_trigger_coverage.py`
- `orchestrator/tests/test_campaign.py`
- `orchestrator/tests/test_buildcache_v2.py`
- 必要なcoverage helper unit test（既存test file内）

buildcacheはsite観測をentryで行うが、valid cache hitはloginでもread-only受理する。
miss判定後、v2の`os.makedirs/claim/staging/_run`、v1のstale clear/configure/buildより前に
loginを拒否する。破損hitはrebuild fallbackせず既存どおり停止する。

指定4 direct coverage helperはtempdir/configure/buildより前にloginを拒否する。
`s8a_trigger_freq` はshared `_build` gateを継承する。computeとotherのbuild argvは
今回変更せず`-j16`のままとする。cache key、contract、completion、BuildResult、
floor/ratified producer、freeze bytesを変更しない。

### U4 — Claude Bash second barrier

所有:

- `hooks/guard_bash.py`
- `orchestrator/tests/test_hooks.py`

Pegasus loginと正直に観測できた場合だけ、既知の直接 `pytest` / `python -m pytest` /
`cmake --build` / `make` / `ninja` / `ctest` をbest-effort拒否する。
repository正規 `tools/run_tests.py`、`submit_tests.py`、qsub、cmake configureは許可する。
policy import/observation失敗時はheavy candidateだけfail-closedにする。

保証外（Codex、任意script、変数、alias、encoded command）はdocsへ明記し、
guardをsystem-wide security boundaryと呼ばない。

### 親所有

- 新decision: login-node execution boundary、named surface、qlogin保留、build jobs据置、
  buildcache/v3裁定パッケージ。
- Pegasus runbook、tools/pegasus README、tests README、phase/worklog/handoff/insights。
- compute node上のtargeted/full/mutation/acceptance receipt。

## 受入

- unit: policy、runner、snapshot、scheduler、build miss、hookの正負境界。
- live: loginからdirty snapshotのtargeted runnerを投入し、qstat可視、bnode/PBS/affinity、
  Python/plugin、snapshot SHA、child rc、stdout/stderr/accounting、task-run attempt一回を確認。
- live control: submit後に元test bytesを変えてもsnapshot側bytesを実行する。
- build/test/mutation/full suite、`check_codex_agents.py`、`check_docs.py` はcompute nodeで実行。
- commit後`check_ai_provenance.py`を実行し、最新main統合tipをcomputeで再受入する。

## 段4で実装しない裁定パッケージ

1. `buildcache/v3` atomic producer receipt、actual/reproduction argv分離、
   manifest/result provenance v3、valid v3 hit受理、legacy official拒否。
   推奨はreceipt-required v3で、fresh-only案は棄却。
2. qloginのhostname/PBS/affinity実測とmarkerless compute受理。
3. t152、silo ladder、全direct compiler/build routeの共有gateまたは自動dispatch。
4. scheduler/PAM/cgroup等のsystem-wide login load enforcement。
5. adversarial writerに対する真の瞬間filesystem snapshot。
