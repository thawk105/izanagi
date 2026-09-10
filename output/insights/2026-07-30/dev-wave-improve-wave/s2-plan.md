親 brief と指定規律、実装・tests・producer/consumer を静的に追跡し、段3へ渡せる実装計画として閉じました。dev-wave の段2規律に従い、ファイル変更、pytest、ビルド、mutation 実行はしていません。したがって緑は主張しません。

指定された `docs/runbooks/pegasus.md` は存在しません。リポジトリの正本として [docs/README.md:34](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/docs/README.md:34) から参照される [docs/pegasus-runbook.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/docs/pegasus-runbook.md:1) を読みました。

## 現状の制御流と root cause

テスト経路は現在、次の順で常に呼出し元ノード上で動きます。

`run_tests.main → argv 正規化 → deletion/ruleops/submodule preflight → xdist 確認・pip 自動導入 → -n 最大32 → pytest → task-run`

根拠は [tools/run_tests.py:784](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:784) です。site 分岐がなく、ログインノードで preflight、pip、pytest、task-run がすべて走ります。[CPU 解決:106-137](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:106) は affinity を見るものの上限32、[xdist 処理:162-173](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:162) は network 利用可能性を前提にします。

ビルド側の root cause は以下です。

- v1 `build()` は [buildcache.py:564-626](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:564) で既定 `jobs=16`。site 判定はありません。
- v2 は [buildcache.py:335-367](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:335) で `-j16` を再生成します。
- v2 fresh build の実 argv は `.staging-*` を使う [buildcache.py:487-501](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:487) 一方、返却 provenance は publish 後の final `bdir` と既定 `-j16` で再構成されます。すでに実行 argv と不一致です。
- coverage の4経路は [s2:230-250](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s2_verify_calibration.py:230)、[s3:123-137](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s3_lock_coverage.py:123)、[s5:119-133](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s5_permutation_coverage.py:119)、[s8a:90-106](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8a_trigger_coverage.py:90) で直接 `-j16` を組み立てます。
- [guard_bash.py:361-427](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/hooks/guard_bash.py:361) は防護 path の字面がなければ即許可するため、直接 pytest/build は管轄外です。
- 既存 Pegasus submitter は用途別・非同期で、dirty snapshot、同期 child rc、timeout/interrupt qdel を一つのプロトコルとして持ちません。例は [submit_certify.sh:170-236](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/submit_certify.sh:170) です。

## site policy の設計

新規 `orchestrator/campaign/pegasus_policy.py` を stdlib-only の最下層 module とします。

API は次で固定します。

- `SiteKind`: `PEGASUS_LOGIN | PEGASUS_COMPUTE | OTHER`
- `SiteObservation`: raw/normalized hostname、raw/normalized PBS ID、affinity CPU tuple、CPU count、観測 source、site
- `SitePolicyError`: 観測不能・Pegasus identity 不整合
- `observe_site(...)`: hostname、environment、`sched_getaffinity` を注入可能にして観測
- `classify_site(hostname, pbs_jobid, affinity, fallback_cpu_count)`: 純関数
- `test_default_jobs(observation, other_cap=32)`
- `resolve_build_jobs(explicit_jobs, observation=None)`

分類規則は closed set とします。

- login: `pegasus01/02/03` またはその exact `ccs.tsukuba.ac.jp` FQDN。PBS ID があれば mismatch で拒否。
- compute: `bnode[0-9]{3}` または exact FQDN。PBS ID は `(?:0:)?[0-9]+\.nqsv` 必須、affinity は空でない実測集合必須。
- other: 上記 hostname に exact match しないもの。PBS があっても P3 に従い other。
- Pegasus hostname で affinity 観測不能、compute で PBS 欠落・不正、login で PBS 存在は fail-closed。
- DNS lookup はせず、短縮名/FQDN の exact lexical 判定だけを使います。
- `0:` は先頭一回だけ除去して PBS ID を正規化します。

jobs の解決は次です。

| site | tests default | build default |
|---|---:|---:|
| login | local 実行不可 | 呼出し自体を拒否 |
| compute | `len(sched_getaffinity(0))` | 同左 |
| other | `min(available, 32)` | 16 |

明示 `-n` / `IZANAGI_TEST_NPROC` / `jobs` は正値検証後に優先します。ただし login 拒否を先に行い、明示値による bypass は許しません。compute で明示値が affinity を超えても P2 に従い受理し、oversubscription として receipt に記録します。

依存方向は一方向です。

```text
campaign/pegasus_policy.py  （stdlib のみ）
├── tools/run_tests.py
├── tools/pegasus/{submit_tests,test_dispatch}.py
├── campaign/{buildcache,pipeline,coverage modules}
└── hooks/guard_bash.py
```

policy から runner、buildcache、hook、PBS tool への逆 import は禁止します。

## dispatch の状態機械と失敗時挙動

| 状態 | 処理 | 失敗時 |
|---|---|---|
| S0 | site と argv を分類。no-execution 形は login でも local | 不正 `PYTEST_ADDOPTS` は qsub 前に rc 2 |
| S1 | dirty state を isolated snapshot に固定 | snapshot 不整合なら qsub せず infra failure |
| S2 | `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` と pre-submit receipt | 1つでも失敗すれば qsub しない |
| S3 | exact snapshot 内 job script を `gen_S`、1 node、policy walltime で qsub | qsub 非0は記録して infra failure |
| S4 | ID を厳密 parse、`qstat -f` 可視性・request を確認後に submit receipt を publish | ID 既知なら qdel。ID 不明なら orphan-risk receipt |
| S5 | job が receipt/PBS/source hash/Python/hostname/affinity/qstat resource を検証 | pytest を起動せず job-result failure |
| S6 | marker を設定し snapshot の `run_tests.py` を一回だけ実行 | runner stdout/stderr/rc を必ず固定 |
| S7 | terminal/disappearance 後、`.o/.e` 安定化・accounting・post-budget を検証 | 不足 receipt は子出力が緑でも infra rc 125 |
| S8 | final receipt、stdout/stderr replay、完全な子 rc を親へ返す | — |

timeout は rc 124、SIGINT は130、その他 infrastructure failure は125とします。S3以降の timeout/INT/TERM は、既知の normalized job ID に対して qdel を一回だけ実行し、その argv/stdout/stderr/rc、terminal poll、accounting の成否を cancellation receipt に残します。取消開始後に遅れて success receipt が現れても成功へ反転しません。

### isolated snapshot

snapshot は `output/env/pegasus/test-dispatch/<nonce>/` 配下の private create-only namespace とします。

1. local repository から `git clone --no-local --no-checkout` し、HEAD を detached checkout。network、alternates、remote fetch は使わない。
2. staged diff を `git diff --cached --binary --full-index --no-ext-diff --no-textconv`、unstaged diffを別 patchとして clone 側へ順番に適用する。
3. nonignored untracked filesを NUL 区切り inventory、`lstat → O_NOFOLLOW read/hash → lstat` で固定する。削除・mode・symlink も manifest に含め、snapshot 外へ逃げる symlink は拒否する。
4. `external/ccbench` は superproject と別に local cloneし、gitlink `d706650…`、内部 staged/unstaged/untracked bytesを同じ方法で固定する。alternates は禁止。
5. ignored input は documented な `output/runs/silo-sample` だけ、存在時に明示 inventory として含める。build cache、dispatch runtime、`.venv` 等は含めない。
6. source root を再走査し、最初の HEAD/index patch/worktree patch/untracked/submodule manifest と完全一致しなければ投入しない。
7. compute 開始直前にも snapshot bytes/mode/hash を検証する。以後、テスト自身が snapshot 内 submodule を一時変更することは許すが、共有 worktree は一切実行対象にしない。

snapshot manifest は HEAD、relative path、mode、SHA-256、各 patch SHA、submodule identity、runner/job script/policy SHAを束縛します。snapshot と receipt は自動削除せず、後日の監査に残します。

### 再 dispatch 防止 marker

`IZANAGI_PEGASUS_TEST_DISPATCH=v1:<nonce>:<source_manifest_sha256>` を worker だけが設定します。

- login + marker: bypass 試行として拒否。
- other + marker: 拒否。
- compute + marker: submit receipt、job ID、nonce、source hash と完全一致した場合だけ local runner へ進む。
- compute で marker なし: qlogin 等の直接 compute 実行として local 実行可。
- login executing shape: preflight より前に submitter を同期呼出し。
- login no-execution shape: qsubせず現行CLIをlocal実行。

これにより deletion/ruleops/submodule preflight、xdist確認、pytest、task-run は compute 側の一回だけになります。`IZANAGI_TASK_RUNS_ROOT` は snapshot 外の元 repository の durable output へ明示し、task-run の実行場所は compute、保存先は永続領域とします。

### submitter の実行契約

新規 `tools/pegasus/submit_tests.py`、`test_dispatch.py`、`run_tests_job.sh` を追加します。

- job 内では `/usr/bin/python3.10`、`python3.10`、`python3` の候補から Python >=3.10 かつ pytest、packaging、pytest-xdist >=2.5 が同じ interpreter にあるものだけを選択。
- compute で pip、git fetch、FetchContent 等を行わない。依存不足は直列fallbackでなく infrastructure failure。
- `#PBS -A SFC`、`#PBS -q gen_S`、`#PBS -b 1`、policy walltime を static test で照合。
- parent/worker 双方の `qstat -f` で account code、queue、1 node、CPU Max 48、bnode hostname、normalized IDを確認。
- worker の `sched_getaffinity(0)` は48件であることを policy の `expected_physical_cores` と照合。
- default pytest argv は `-n 48`。明示 `-n` の場合は値を尊重し、`nproc_source=explicit` として記録。
- runner stdout/stderr、PBS `.o/.e`、child rc、Python path/version、affinity list、exact pytest argv、preflight/task-run attemptを別々の create-only receipt にする。
- accounting は exactly one Request ID、Started、Ended、Elapse を要求し、qsub ID と照合する。[既存 accounting 規約](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/silo_ladder_rung1.py:3662) と同じ意味論を使う。
- NQSV accounting は pytest rc の正本にしない。child rc の正本は hash-bound `runner-result.json`。
- receipt は temp+fsync+no-replace publish、各段を前段SHAへ鎖状に束縛する。
- `qsub -V` は使わない。PATH、locale、test trigger、task-run、nproc、`PYTEST_ADDOPTS` 等のclosed allowlistだけをprivate env receipt経由で渡し、proxy/token/元repo `PYTHONPATH` は渡さない。

## file:line 単位の変更計画

### U1 — site policy

| file:line | 変更 |
|---|---|
| `orchestrator/campaign/pegasus_policy.py` 新規 | 上記 enum、observation、分類純関数、test/build jobs resolver、注入可能な観測API |
| `orchestrator/tests/test_pegasus_policy.py` 新規 | hostname/PBS/affinity matrix、spoof、fallback、jobs precedence、import境界 |
| [policy.json:1-14](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/policy.json:1) | `test_dispatch` の queue/project/node/walltime、expected affinity、poll/grace timeoutを追加 |

### U2 — runner / submitter

| file:line | 変更 |
|---|---|
| [run_tests.py:1-22](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:1) | login dispatch、compute network非依存、other互換のdocstring |
| [run_tests.py:83-94](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:83) | no-execution/PYTEST_ADDOPTS/外部pathの早期分類を純関数化 |
| [run_tests.py:106-137](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:106) | policy observationへ統合。compute affinity全数、other cap32 |
| [run_tests.py:162-173](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:162) | computeではinstall禁止・依存不足hard fail、otherは現行fallback |
| [run_tests.py:235-294](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:235) | CLIと`PYTEST_ADDOPTS`の明示 `-n` を検出し、default injectionとのprecedenceを固定 |
| [run_tests.py:724-830](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:724) | login dispatchをpreflight前へ置き、marker検証、runner/task-run一回をreceipt化 |
| `tools/pegasus/test_dispatch.py` 新規 | snapshot、hash、receipt、qsub/qstat/qdel/accounting parser、同期controller |
| `tools/pegasus/submit_tests.py` 新規 | production CLI、worker mode、signal/timeout処理、stdout/stderr replay、rc伝播 |
| `tools/pegasus/run_tests_job.sh` 新規 | PBS request、Python3.10 gate、`/scr/<colon-safe-job-id>`、worker一回実行 |
| [.gitignore:22-25](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/.gitignore:22) | `output/env/pegasus/test-dispatch/` をruntimeとしてignore |
| [test_run_tests_nproc.py:40](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_run_tests_nproc.py:40) | site別default、CLI/env/PYTEST_ADDOPTS precedence |
| [test_run_tests_preflight.py:595](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_run_tests_preflight.py:595) | loginではpreflight前dispatch、compute markerでは各preflight一回 |
| [test_run_tests_task_run.py:1](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_run_tests_task_run.py:1) | task-run一回・durable root・子rc |
| `orchestrator/tests/test_pegasus_test_dispatch.py` 新規 | fake scheduler/clock/filesystemによる状態機械テスト |
| [test_pegasus_tools.py:25](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_tools.py:25) | 既存real qstat fixtureでresource parser、PBS directive、accountingを固定 |

### U3 — build jobs / provenance

| file:line | 変更 |
|---|---|
| [buildcache.py:138-155](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:138) | `cached=false` の argv は実行argvそのもの、`cached=true` は再現用である意味論を明示 |
| [buildcache.py:335-367](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:335) | `_v2_commands` のjobs既定を廃止。`_v2_result` に実argvを渡し再構成しない |
| [buildcache.py:407-561](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:407) | `jobs=None`追加、entry先頭でpolicy解決、freshのstaging argvをそのまま返す |
| [buildcache.py:564-626](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:564) | v1もentry先頭で解決。loginはcache hitを含め呼出し拒否、other16、compute affinity |
| [pipeline.py:363-375](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/pipeline.py:363) | `build_jobs=None`をadditive追加 |
| [pipeline.py:414-516](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/pipeline.py:414) | WAL/source処理前にsite gateし、v1/v2のtrace/perfへ同じjobsを渡す |
| [s2_verify_calibration.py:230-274](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s2_verify_calibration.py:230) | mainで一度解決しstock/broken全buildへ伝播 |
| [s3_lock_coverage.py:123-164](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s3_lock_coverage.py:123) | 同上 |
| [s5_permutation_coverage.py:119-160](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s5_permutation_coverage.py:119) | 同上 |
| [s8a_trigger_coverage.py:90-106](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8a_trigger_coverage.py:90) | `_build(..., jobs=None)`を追加しshared resolver利用 |
| [s8a_trigger_freq.py:60-145](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8a_trigger_freq.py:60) | import consumerからexplicit jobsを共有helperへ通す |
| [s8b_floor_campaign.py:962-1019](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8b_floor_campaign.py:962) | `require_fresh_provenance`を追加しofficialでは`cached=true`をmanifest前に拒否 |
| [s8b_floor_campaign.py:1126-1156](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8b_floor_campaign.py:1126) | 実argvに既存のtoken単位portable変換だけを適用 |
| [s8b_floor_campaign.py:2938-2996](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8b_floor_campaign.py:2938) | fresh/resume双方でofficial fresh gateを伝播 |
| [s8b_ratified_freeze.py:1624-1667](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8b_ratified_freeze.py:1624) | ratifiable generationの`cached=true`を意味的に拒否 |
| [test_buildcache_v2.py:91](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_buildcache_v2.py:91) | jobs/site/fresh actual argv/completion不変 |
| [test_campaign.py:2829](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_campaign.py:2829) | cache key golden不変、v1 jobs/site、pipeline早期拒否 |
| [test_s8b_floor_campaign.py:2347](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_s8b_floor_campaign.py:2347) | portable(actual argv)、official cached拒否、manifest/result mirror |
| [test_s8b_ratified_verify.py:266](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_s8b_ratified_verify.py:266) | cached generationとbuild_argv driftの拒否 |

### U4 — guard

| file:line | 変更 |
|---|---|
| [guard_bash.py:92-125](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/hooks/guard_bash.py:92) | wrapper剥離を再利用し、pytest/python-m-pytest/cmake--build/make/ninja/ctest分類を追加 |
| [guard_bash.py:361-427](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/hooks/guard_bash.py:361) | protected-path fast pathより先にPegasus login heavy gate。compoundと一段shell `-c`も検査 |
| [guard_bash.py:430-445](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/hooks/guard_bash.py:430) | heavy候補でsite観測不能ならfail-closed |
| [test_hooks.py:283](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_hooks.py:283) | login拒否、wrapper/compound、sanctioned runner/submitter/qsub許可、other不変 |
| [hooks/README.md:59-72](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/hooks/README.md:59) | login-node load gateと既知限界を追記 |

### 親が所有する文書

- [docs/pegasus-runbook.md:252-271](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/docs/pegasus-runbook.md:252): 2026-07-27の「loginでbuild/test可」を最新裁定で置換。
- [docs/pegasus-runbook.md:317-344](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/docs/pegasus-runbook.md:317): PBS ID、Python、network、snapshot。
- [docs/pegasus-runbook.md:346-366](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/docs/pegasus-runbook.md:346): receipt/qstat/accounting/qdel checklist。
- [tools/pegasus/README.md:70](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/README.md:70): test dispatch CLI・state・receipt。
- [orchestrator/tests/README.md:16-32](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/README.md:16): site別runner規約。
- `docs/decisions.md`、`docs/phase3.md`、`docs/worklog.md`: 最新裁定・実測・mutation結果を親が記録。

## 所有非重複の実装単位と依存順

1. U1が policy module と純粋境界testだけを所有。
2. U2が runner、snapshot、PBS submitter、receipt、markerを所有。
3. U3が buildcache、pipeline、coverage jobs、floor/ratified provenanceだけを所有。
4. U4が guard判定核とhook testだけを所有。
5. 親がdocs、実機receipt、phase/worklog、commitを所有。

依存順は `U1 → U2/U3/U4 → producer/consumer閉包確認 → docs → compute tests/mutation/実機受入 → commit同梱検査` です。U2/U3/U4間で編集ファイルは重複させません。

## 追加・変更するテスト

- site matrix: short/FQDN、大文字・末尾dot、spoof suffix、login+PBS、compute-PBS欠落/不正、other+PBS、空/重複 affinity。
- runner: no-execution local、executing login dispatch、dispatchがpreflightより先、compute marker一回、偽marker、computeでpipを呼ばない。
- explicit override: CLI `-n`、`PYTEST_ADDOPTS -n`、`IZANAGI_TEST_NPROC`、build `jobs`、login bypass不能。
- snapshot: clean、staged、unstaged、untracked、deletion、submodule dirty、symlink escape、copy中変更、freeze後元tree変更、ignored sample、snapshot外target。
- submitter: Python3.9拒否/3.10受理、network callなし、qsub ID parse、qstat visibility、CPU48/host/request照合、stdout/stderr、child rc、accounting。
- failure: pre-submit/submit/job-result/stdout/stderr/final/accounting receipt不足、qstat不一致、PBS ID mismatch、timeout、SIGINT、qdel一回、qdel failure、qsub成功-ID不明。
- v1/v2: other16、compute48、explicit7、login cache hit拒否、jobsをkey/contract/completionへ入れない。
- provenance: v2 `_run` が受けたstaging argvとfresh `BuildResult`のexact一致、portable変換後のfloor一致、official cached拒否。
- coverage: 4helperすべて `-j16/-j48/explicit`、loginではconfigure subprocessすら呼ばれない。`s8a_trigger_freq`の間接consumerも固定。
- hook: absolute path、env/timeout/taskset wrapper、compound、shell `-c`を拒否。cmake configure、qsub、repo正規runner/submitter、other siteは許可。
- frozen sentinel: [test_frozen_artifacts.py:38-85](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_frozen_artifacts.py:38) と exact 23件検査を無変更で通す。
- 新規test fileは自走 harnessを持たせ、[test_plain_runner_coverage.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_plain_runner_coverage.py:1) のallowlistを安易に広げない。

## mutation 計画

| mutation | 殺す検査 |
|---|---|
| hostname regexを部分一致化、spoofをlogin扱い | site matrix |
| login/PBS mismatchをotherへdowngrade | policy・runner・guard |
| affinityを32/16へ固定、off-by-one | runner/build resource tests |
| explicit jobsをdefaultで上書き、login bypass許可 | precedence tests |
| dispatchをpreflight後へ移動、marker検査除去 | preflight/task-run count |
| 元worktreeをcomputeで直接使用 | source-root/snapshot mutation |
| untracked/deletion/submodule/二回目scanを省略 | dirty snapshot matrix |
| computeでpip fallbackを復活 | network-independent test |
| Python3.9を許可、qstat確認を省略 | job preflight tests |
| receipt不足を成功扱い、child rcを0へ置換 | receipt/rc tests |
| qdelを省略または二重実行 | timeout/interrupt tests |
| jobsをcache key/contract/completionへ追加 | golden/exact-key tests |
| fresh v2 argvをfinal pathで再構成 | `_run` argv exact test |
| official cachedを許可 | floor/ratified negative tests |
| guard heavy gateをfast path後へ戻す | direct pytest/build tests |
| wrapper/compound/shell-cを見ない | adversarial hook tests |
| cmake configure/qsubまで過剰拒否 | false-positive tests |

## 凍結・producer/consumer・provenance 閉包

将来の正しい列は次です。

`buildcache._run(actual argv) → fresh BuildResult argv → build_cells → token単位portable変換 → manifest.binaries → result.binaries mirror → ratified validator`

- `cache_key` [buildcache.py:121-135](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:121)、v2 identity、contract、`completion.json` exact keys [buildcache.py:527-538](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:527) は不変。
- jobs は上記 identity/completionへ入れず、fresh floorのportable `build_argv`だけに現れます。
- cache hitから過去の実jobsは復元できないため、official floorはfreshのみ。pilotのcached表示はratifiable provenanceではありません。
- manifest/result mirrorは [floor campaign:1175-1197](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8b_floor_campaign.py:1175) と result側の既存照合を維持します。
- ratified portable key集合 [s8b_ratified_freeze.py:181-185](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8b_ratified_freeze.py:181) は変更せず、`cached` の意味検証だけ強化します。
- active v2 generationなし・official accepted set空なので、既存generation/floorの再発行はしません。
- `FROZEN_MANIFEST` 23件、protocol、selector、v1 freeze、既存env/campaign JSON、fixture WALの歴史的 `-j16` は一切編集・再生成しません。

## 段3で攻撃すべき provisional assumptions

- P1: 自動dispatchが `run_tests.py` だけで十分か。campaignの早期site gateより前に別producerが書かないか。
- P2: explicit `-n auto`、0、affinity超過を無条件にcaller裁定とすることが妥当か。
- P3: unknown hostname + NQSV PBS IDをotherとして許す規則が、新compute hostname追加時に過少防御にならないか。
- P4: dirty snapshotがindex/worktree/submodule/mode/symlink/ignored inputの全意味を再現するか。
- `PYTEST_ADDOPTS` のargsfile、外部plugin、外部rootdirがsnapshot外sourceを再導入しないか。
- closed env allowlistで元実行との意味が変わらないか、secretを漏らさないか。
- qstatのpending/running/disappearance、scheduler logの遅延、accounting footerの安定化判定。
- one node=CPU48は実測事実だが、`Exclusive submit=OFF`で専有を意味しない点。
- compute側にPython3.10+pytest+xdistが常備される前提。欠けた場合は自動導入せず停止すること。
- official fresh-only gateがpilot cache混在時に運用上理解可能なエラーを返すか。
- coverage driversが `ENV_TAG=linux-baremetal` を固定しているため、Pegasus実走出力を公式linux-baremetal証拠に誤採用しないか。
- guardはテキスト防壁であり、alias、動的変数、別名script、encoded `python -c`を完全には封鎖できない点。

## scope 外

- Codex hook adapter・`.codex/hooks.json`・native role再配線。既存の [未配線規約](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/hooks/README.md:15) は不変。
- 任意campaign/buildの自動qsub化。loginでは拒否するだけ。
- 既存certify/floor/silo submitterの全面共通化。
- active v2 generation作成、official floor再発行、凍結bytes・歴史成果物の更新。
- submodule pin `d706650` の変更。
- 48 workerの性能優位、node専有、throughput改善の主張。
- `t152_write_intent_coverage.py` の独自 `DEFAULT_JOBS=8`。親briefのcoverage 4経路ではないため変更しない。
- Pegasus向けcoverage env tag再設計。実出力を公式証拠にする場合は別裁定が必要。
- compute nodeへのpackage/network provisioning。
- push。リポジトリ規律どおり人間が行う。

## リスクと受入条件

主要リスクは、dirty snapshotの意味保存、qstat/accountingの非同期race、cached provenanceの誤称、guardのshell解析限界です。いずれも「曖昧なら成功にしない」「既知IDならqdel」「receiptが欠ければ子出力に関係なくinfra failure」で閉じます。

段3以降の受入条件は次です。

1. 上記unit/integration/mutationをPegasus computeで実行し、site・jobs・receipt・frozen sentinelを確認。
2. loginから executing `run_tests.py` を呼び、qsubが可視、computeがbnode/PBS/affinity48/Python>=3.10、default argvが`-n48`、preflight/task-runが一回であること。
3. no-execution形ではqsubが一件も発生しないこと。
4. dirty tree投入後に元treeを変更しても、jobがmanifest固定snapshotだけを実行すること。
5. stdout/stderr、exact child rc、PBS `.o/.e`、accounting、post-budget、final receiptが揃うこと。
6. timeout/interruptでqdel一回とcancel receiptが残ること。
7. build v1/v2と4 coverageでcompute48、other16、explicit優先、login拒否。
8. fresh v2の実argvとfuture floor portable `build_argv`が一致し、official cached provenanceが拒否されること。
9. frozen 23件とprotocol/selector/v1 bytesのSHAが不変。
10. 関連検査後に `tools/check_codex_agents.py`、`tools/check_docs.py`、commit後に `tools/check_ai_provenance.py` を親が実行すること。

## 総括

実装の中心は、単一のfail-closed site policy、dirty bytesを固定する同期PBS dispatch、全build経路の共通jobs解決、fresh-onlyの正直なfloor provenanceです。既存凍結・歴史出力・Codex hook配線には触れず、実測と緑判定は段3以降のPegasus計算ノードへ委ねます。