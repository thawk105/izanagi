## 総括

結論は、S1・S2・S3・S5 は実装可能ですが、**S4 は現 brief の不変条件と両立しません**。`jobs` は cache identity には入りませんが、`build_argv` を経由して floor の manifest・result、さらに ratified generation の `floor_source` に凍結されます。ユーザー指定の「入るなら scope を止める」に該当するため、段 5 は親の brief 改訂まで開始すべきではありません。

| Scope | 実装要点 |
|---|---|
| S1 | 新規 `orchestrator/campaign/site_policy.py`。stdlib-only leaf とし、[run_tests.py:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:41) から軽く import、[buildcache.py:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:26) から相対 import |
| S2 | [run_tests.py:784–830](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:784) の既存 preflight 後・xdist 前へ dispatch gate。新 rc=16。task_run は計算ノード側だけで一度記録 |
| S3 | 新規 `tools/pegasus/dispatch.py`。gen_S、1 node、2時間、qsub→即時 qstat→compute marker→release→`.o/.e`・会計収集→子 rc 伝播 |
| S4 | [buildcache.py:335](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:335)、[同:564](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:564) と coverage 4 箇所が対象。ただし凍結連鎖への流入が判明したため blocking |
| S5 | [guard_bash.py:361–427](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:361) の root 解決直後・既存 fast path 前へ、Pegasus login 限定の token 判定を追加 |

`jobs` の裏取り結果は次のとおりです。

- `cache_key()` の preimage は genome・commit・trace・source・toolchainだけで、`jobs` はありません。[buildcache.py:121–135](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:121)

- v2 identity にもありません。[buildcache.py:219–234](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:219)

- `contract_sha256` は dataclass 全 field の hash ですが、その field 集合に `jobs` はありません。[env_contract.py:97–102](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/env_contract.py:97)、[同:145–160](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/env_contract.py:145)

- buildcache v2 completion manifest にもありません。[buildcache.py:527–538](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:527)。既存独立 golden も `jobs` を含みません。[test_s8b_protocol_builder.py:47–63](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_s8b_protocol_builder.py:47)

- しかし実際の `-j N` は `BuildResult.build_argv` に入り、[buildcache.py:347–364](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:347)、floor manifest の `binaries[*].build_argv` へ保存されます。[s8b_floor_campaign.py:1004–1014](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s8b_floor_campaign.py:1004)、[同:1146–1155](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s8b_floor_campaign.py:1146)。ratification はこれを manifest の正式 field とし、[s8b_ratified_freeze.py:181–194](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s8b_ratified_freeze.py:181)、result と manifest の一致を要求し、[同:3032–3035](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s8b_ratified_freeze.py:3032)、その result raw bytes を `floor_source` として凍結します。[同:1321–1339](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s8b_ratified_freeze.py:1321)

最大リスクは次の3件です。

1. S4 の `-j 48` が proof-chain 成果物へ正直に現れるため、現 brief の「凍結 manifest に入らない」と両立しない。
2. 計算ノードの Python 3.10 に pytest・packaging・pytest-xdist が揃っていない場合、外部 network 不可のため dispatcher が自己修復できない。
3. qsub 後の qstat消失、`.o/.e` 遅延、会計欠落、割込み時の qdel失敗により orphan job または F49 型無効セッションになり得る。

brief への反論は**あり**です。S4 が blocking、S5 の「全直接重量コマンド」は text hook の既知限界上、完全保証ではなく defense-in-depth としてのみ成立します。

## S1 — policy 単一正本

### 配置

新規 `orchestrator/campaign/site_policy.py` に置きます。現時点では新規ファイルなので実在行番号はありません。

根拠は以下です。

- `buildcache.py` は既に campaign 内 leaf を相対 import しています。[buildcache.py:26–28](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:26)

- `campaign/__init__.py` は説明 docstring だけで、DB・WAL・model 等を eager importしません。[campaign/__init__.py:1–20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/__init__.py:1)

- stdlib-only leaf の先例が `env_contract.py` に明記されています。[env_contract.py:1–17](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/env_contract.py:1)

- tools 側が repo root または `orchestrator` を `sys.path` へ足して import する規約は実在します。[check_codex_agents.py:30–34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/check_codex_agents.py:30)、[make_acquisition_receipt.py:15–20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/make_acquisition_receipt.py:15)

したがって `run_tests.py` は `_REPO` 確定直後の [run_tests.py:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:41) で repo root を `sys.path` に追加し、`from orchestrator.campaign import site_policy` とします。`buildcache.py` は [buildcache.py:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:26) に `from . import site_policy` を足します。

policy は stdlib の `os/socket/re/typing` だけに限定します。`run_tests.py` の現行軽量 import 面 [run_tests.py:24–39](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:24) に buildcache・model・WALを流入させません。

### サイト判定

新設する最小 API は以下です。

- `classify_site(hostname, pbs_jobid) -> str`
- `current_site(*, hostname_fn=socket.gethostname, environ=os.environ) -> str`
- `is_pegasus_site(site)`
- `is_compute_node(site)`
- `available_cpus(...)`
- `default_test_jobs(site, cap=32)`
- `default_build_jobs(site)`
- login-node refusal message helper

区分は文字列定数にします。`campaign.site_policy` と `orchestrator.campaign.site_policy` の二重 module 名で読み込まれても、Enum class identity の不一致を起こさないためです。

判定条件は次で固定します。

- hostname は `socket.gethostname()` の小文字化・末尾dot除去後、最初の label を使う。DNS問い合わせを伴う `getfqdn()` は使わない。

- `pegasus01` / `pegasus02` / `pegasus03` の exact matchを login とする。短名と `pegasus01.ccs.tsukuba.ac.jp` の双方を受ける。実測名は [runbook:9–14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:9) にあります。

- compute は `^bnode[0-9]{3}$` **かつ** `PBS_JOBID` が `^0:[0-9]+\.nqsv$` のときだけとする。PBS ID の実測形は [runbook:317–321](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:317) です。

- `bnodeXXX` 単独、PBS ID 単独、`pegasus04`、共通名 `pegasus`、hostname取得失敗は `OTHER`。

FQDN必須より「raw hostname + scheduler固有ID」の連言が誤判定に強い設計です。計算ノードでは外部 DNS が使えない実測があり、[runbook:341–344](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:341)、FQDN解決を必須にすると本物の compute を false-negative にし得ます。一方、`bnodeXXX` だけでは他クラスタを誤認するため採りません。

判定不能時は `OTHER` への fail-open とします。未知 host を fail-closed にすると、brief の「非 Pegasus 環境の挙動は不変」[brief.md:33–40](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/brief.md:33) を破るためです。ただし exact login と判定した後の test/build gate・dispatch失敗は fail-closed とします。

`available_cpus()` は現行 [run_tests.py:106–120](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:106) を policy へ移し、`os.process_cpu_count`→`sched_getaffinity`→`os.cpu_count` の順を維持します。

## S2 — `run_tests.py`

### gate の挿入点と rc

- rc定数群 [run_tests.py:95–100](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:95) に `_PEGASUS_DISPATCH_RC = 16` を追加します。13/15/14は既存 preflight、16は site/dispatcher/bootstrap/accounting failure 専用です。実 pytest子rcは変換しません。

- `main()` の [run_tests.py:786–794](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:786) にある deletion→RuleOps→submodule の順序を維持します。

- その直後、xdist準備開始 [run_tests.py:796](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:796) より前へ `_maybe_dispatch_pegasus()` を挿します。これにより login node では pip・pytest・collectionを開始する前に qsub へ移れます。

- `main(argv, *, site=None, dispatch_fn=None)` の keyword-only seam を加え、production の `site=None` は `current_site()`、テストは site と fake dispatcher を直接注入します。

### dispatch 対象

`_has_no_execution_flag()` の既存閉集合 [run_tests.py:357–364](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:357) をそのまま使い、CLI引数だけでなく `PYTEST_ADDOPTS` も判定します。

- `--collect-only`、`--co`、`--help`、`--version`、`--setup-only`、`--setup-plan`、`--fixtures`、`--markers`、`--trace-config` は login node 内で現行経路を継続。

- それ以外は targeted/full、件数、`-k`、単一 nodeid を問わず dispatch。

- `_is_acceptance_run()` [run_tests.py:367–425](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:367) は既存 preflight の発火だけに使い、dispatch可否には使いません。

- `_is_full_suite()` [run_tests.py:297–335](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:297) は task_run の suite identity 用のままです。

compute node では dispatchせず、`_NPROC_CAP=32` [run_tests.py:44–47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:44) を外して affinity 全数を既定にします。明示 `-n` が後勝ちする既存規約 [run_tests.py:282–294](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:282) と既存 `IZANAGI_TEST_NPROC` 明示上書きは維持し、非 Pegasus は現行 cap32を維持します。

compute node では `_ensure_xdist()` の pip導入 [run_tests.py:162–173](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:162) を呼びません。pytest-xdist不在または `<2.5` なら直列fallbackせず rc16。外部 network 不可かつ「最大並列」を満たせないためです。

### task_run 台帳

親 login process は dispatcher の戻り値を受け取って [run_tests.py:821–830](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:821) より前に returnするため、台帳を書きません。

計算ノード側が同じ `run_tests.py` を再実行し、`IZANAGI_TASK_RUN_ID` があれば `_call_and_record()` [run_tests.py:724–781](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:724) から `_record_task_run()` [同:693–721](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:693) を一度だけ呼びます。

dispatcher requestへ渡す環境は `IZANAGI_TASK_RUN_ID`、`IZANAGI_TASK_RUNS_ROOT`、`IZANAGI_TEST_TRIGGER`、`PYTEST_ADDOPTS` の閉じた allowlist とします。親の全環境・秘密・sidecar pathは渡しません。dispatch自体が失敗した場合は test run が存在しないので task_run は作らず、dispatch receiptだけを残します。

## S3 — dispatcher

新規 `tools/pegasus/dispatch.py` を作ります。現時点では新規ファイルなので行番号はありません。

### 投入仕様

- 永続 root: `output/pegasus-dispatch/submissions/<nonce>/`
- project: `SFC`
- queue: `gen_S`
- node: `#PBS -b 1`
- walltime: `#PBS -l elapstim_req=02:00:00`

2時間は既存 policy の certify/rung1 で実在する値です。[policy.json:2–8](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/policy.json:2)。`policy.json` 自体は変更せず、新しい frozen/hash波及を作りません。

処理順は以下です。

1. repo realpath配下かつ `/tmp`・`/scr` でないことを検証し、nonce leafを mode 0700、create-onlyで作る。request JSON・PBS script・pre-submit recordを書いて file/dirを fsyncする。

2. `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` を全て captureし、一つでも非0なら qsubしない。既存作法は [submit_certify.sh:103–125](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/submit_certify.sh:103)。

3. submission dirを cwdとして `qsub dispatch.sh`。request ID parserは既存の `Request <id> submitted` / 単一token規約 [submit_certify.sh:191–205](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/submit_certify.sh:191) と一致させる。

4. `normalize_request_id()` [schema_v2.py:310–316](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/calibrator/schema_v2.py:310) を使い、直後に `qstat -f`。同型の実装は [submit_silo_ladder_rung1.sh:431–439](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/submit_silo_ladder_rung1.sh:431)。

5. jobはまず hostname・raw `$PBS_JOBID` を submission dir の create-only markerへ書き、release待ちに入る。親は markerを policyで `PEGASUS_COMPUTE` と判定し、submit receiptとqstat captureの永続を確認してから release fileを書く。これで F49(ii)(a)(b) を「親fsync + compute nodeからの共有FS書込み + qstat可視」の3点で機械化する。[runbook:358–366](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:358)

6. job内は `python3.10`、`/usr/bin/python3.10`、投入元 `sys.executable` の候補を版数と `pytest/xdist/packaging` importで検査し、3.10以上の実体だけを使う。pipは実行しない。実測差は [runbook:157–162](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:157)。

7. argvはJSON listから直接 `subprocess` へ渡し、PBS scriptへ shell interpolationしない。`/scr/izanagi-test-${PBS_JOBID//:/_}` を一時領域にし、raw IDの `:` を除去する。[runbook:317–321](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:317)

8. 終了後は `dispatch.sh.o<ID>` / `.e<ID>` の full ID・prefix ID・正規化ID候補から、それぞれ通常ファイルを一意に選ぶ。命名規約は [runbook:103–106](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:103)。

会計は既存 `_accounting_summary()` [collect_receipt.py:67–73](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/collect_receipt.py:67) と `_scheduler_name_matches()` [同:101–105](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/collect_receipt.py:101) を再利用します。会計が確認できて初めて子rcをそのまま返します。会計・result・logs・job ID照合のどれかが欠ければ rc16です。

F49(a)(b)(c) のいずれかが失敗した場合は `output/pegasus-dispatch/submission-disabled.json` をcreate-onlyでラッチし、以後の自動qsubを止めます。preflightや子pytest失敗は有効セッション否定ではないため、このラッチ対象にしません。

SIGINT/SIGTERM、親側timeout、release前失敗では normalized IDに `qdel` をbest-effort実行し、captureを永続化します。SIGINTは130、SIGTERMは143。qdel失敗・ID parse不能は orphanの可能性があるため submission-disabledラッチと生qsub出力を残します。

## S4 — build並列度と login拒否

### Blocking evidence

現 brief のまま実装してはいけません。

`jobs` は identityには入りませんが、実行 provenanceには入ります。

```text
jobs
  → BuildResult.build_argv
  → floor manifest.binaries[*].build_argv
  → result.binaries
  → result raw SHA / generation.floor_source
```

この値を `-j 16` のまま記録して実際だけ48で走らせる案は、provenanceを偽るため採用不可です。

### 親が不変条件を改訂した場合の条件付き実装

- `_v2_commands(..., jobs: Optional[int] = None)` の [buildcache.py:335–350](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:335) で、`None` のみ `site_policy.default_build_jobs()` へ解決。

- legacy `build(..., jobs: Optional[int] = None)` の [buildcache.py:564–589](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:564) も同じ。明示 `jobs=1` 等は維持。

- coverage literalを以下で置換。

  - [s2_verify_calibration.py:244–250](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s2_verify_calibration.py:244)
  - [s3_lock_coverage.py:123–137](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s3_lock_coverage.py:123)
  - [s5_permutation_coverage.py:119–133](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s5_permutation_coverage.py:119)
  - [s8a_trigger_coverage.py:90–106](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/s8a_trigger_coverage.py:90)

各coverageのconfigure/build `subprocess.run` を既存 `buildcache._run()` へ寄せます。[buildcache.py:739–745](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:739) は実 cmake configure/buildの直前だけで loginを拒否し、cache hitや `_run` をstubした単体テストは拒否しません。`_run(..., site=None)` の正式注入 seamを加え、境界テストは `site=PEGASUS_LOGIN` を直接渡します。

実 `cmake --build` を呼ぶ既存 nodeid は3件です。

- `orchestrator/tests/test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration` [line 2362](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_s8b_floor_campaign.py:2362)

- `orchestrator/tests/test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration` [line 2393](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_s8b_floor_campaign.py:2393)

- `orchestrator/tests/test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2` [line 3822](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_s8b_oracle_driver.py:3822)

`test_buildcache_v2.py` の通常buildは `_fake_build_environment()` が `_run` をstubしています。[test_buildcache_v2.py:64–86](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_buildcache_v2.py:64)。実subprocessを呼ぶ `test_v2_run_helper_enforces_subprocess_timeout_behavior` は Python sleepでありcmakeではありません。[同:189–194](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_buildcache_v2.py:189)

## S5 — `guard_bash`

policy importを追加し、`decide(command, repo_root="", *, site=OTHER)` とします。既存unit testはOTHERのまま安定し、production `main()` [guard_bash.py:430–446](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:430) だけが `current_site()` を明示注入します。

新規判定は root確定 [guard_bash.py:361–364](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:361) の後、既存 `_MENTION_RE` fast path [同:365–366](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:365) より前です。`pytest` 等を `_MENTION_RE` に混ぜず、既存防護対象のerror semanticsを広げません。

既存 `_tokenize()`、`_segments()`、`_head_and_args()` [guard_bash.py:142–196](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:142) を再利用し、segmentごとに判定します。

Pegasus loginで拒否する条件は以下です。

- headが `pytest` / `py.test`、または版付きPythonを含む `python3.10 -m pytest`。ただし既存 `_NO_EXECUTION_FLAGS` 相当は許可。
- `cmake` argsに exact `--build`。
- `make` argsに `-j`、`-jN`、`--jobs`、`--jobs=N`。
- `ninja` 実行。help/versionのみ許可。
- `ctest` 実行。`-N` / `--show-only` / help/versionは許可。
- `perf` の実測subcommand、`build-variants` 配下 executable、basename `ycsb_*.exe`。
- `bash -c` / `sh -c` の内側も深さ上限付きで再tokenize。

sanctioned pathはsegment単位で先に認識します。

- repo内 exact `tools/run_tests.py`
- repo内 exact `tools/pegasus/*`
- head `qsub`

したがって `python3 tools/run_tests.py && pytest -q` は第1 segmentだけ許可し、第2 segmentを拒否します。

境界例は以下です。

- 許可: `python3 tools/run_tests.py -q`、`python3.10 tools/pegasus/dispatch.py ...`、`qsub job.sh`、`pytest --collect-only`、`cmake -S src -B build`、`make help`、`ctest -N`、`rg pytest`。

- 拒否: `pytest -q`、`python3.10 -m pytest`、`cmake --build build`、`make -j48`、`ninja -C build`、`ctest`、`perf stat -- .../ycsb_silo.exe`。

既存 `_BUILDERS` [guard_bash.py:124–125](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:124) の build-variants例外はOTHER/computeで維持し、loginの新判定が先に拒否します。既存 `_INTERP` は非Pegasusの受理集合を変えないため編集せず、版付きPython認識はlogin規則内だけに置きます。

分類・policy import失敗はOTHERへ倒し、全 Bash停止を避けます。run_tests/buildcacheが一次強制、guardは直接tokenの第二防壁です。text guardのscript/変数/glob越し限界は [hooks README:163–190](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/README.md:163) のままです。またCodexには現在未配線です。[hooks README:15–24](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/README.md:15)

## 境界テスト計画

以下は追加予定の nodeid 案です。今回は一件も実走していません。

| Scope | nodeid案 |
|---|---|
| S1 | 新規 `orchestrator/tests/test_site_policy.py::test_login_short_and_fqdn_are_exactly_classified` |
| S1 | `...::test_compute_requires_bnode_and_exact_nqsv_jobid` |
| S1 | `...::test_unknown_hostname_or_resolver_failure_fails_open_to_other` |
| S1 | `...::test_other_defaults_preserve_test_cap32_and_build_jobs16` |
| S2 | `orchestrator/tests/test_run_tests_preflight.py::test_main_dispatch_is_after_rc13_15_14_and_before_xdist` |
| S2 | `...::test_no_execution_shapes_never_dispatch_on_pegasus_login` |
| S2 | `...::test_targeted_and_full_execution_both_dispatch` |
| S2 | `orchestrator/tests/test_run_tests_nproc.py::test_compute_default_uses_all_affinity_while_other_keeps_cap` |
| S2 | `...::test_compute_missing_xdist_is_rc16_and_never_invokes_pip` |
| S2 | `orchestrator/tests/test_run_tests_task_run.py::test_parent_dispatch_does_not_record_and_compute_child_records_once` |
| S3 | `orchestrator/tests/test_pegasus_tools.py::test_dispatch_qsub_qstat_compute_marker_release_and_accounting_chain` |
| S3 | `...::test_dispatch_selects_python310_without_network_or_pip` |
| S3 | `...::test_dispatch_sanitizes_colon_jobid_for_scr` |
| S3 | `...::test_dispatch_propagates_child_rc_exactly_after_accounting` |
| S3 | `...::test_dispatch_missing_accounting_latches_future_submissions` |
| S3 | `...::test_dispatch_interrupt_qdels_normalized_request` |
| S4 | 条件付き新規 `orchestrator/tests/test_build_jobs_policy.py::test_other_stays_j16_and_compute_uses_all_affinity` |
| S4 | `...::test_login_real_cmake_refusal_precedes_subprocess_but_stubbed_run_is_unchanged` |
| S4 | `...::test_four_coverage_builders_use_policy_jobs` |
| S4 | `orchestrator/tests/test_buildcache_v2.py::test_jobs_do_not_change_v2_identity_or_completion_manifest` |
| S4 | `orchestrator/tests/test_campaign.py::test_source_digest_silo8_id_backward_compatible`（既存golden、[line 2920](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_campaign.py:2920)） |
| S5 | `orchestrator/tests/test_hooks.py::test_bash_pegasus_login_direct_heavy_commands_denied` |
| S5 | `...::test_bash_pegasus_sanctioned_dispatch_and_nonexecution_allowed` |
| S5 | `...::test_bash_other_site_preserves_existing_heavy_command_behavior` |
| S5 | `...::test_bash_compound_command_cannot_hide_direct_pytest` |

Pegasus模擬は hostname monkeypatchではなく、S1の `classify_site(hostname, pbs_jobid)`、S2の `main(..., site=..., dispatch_fn=...)`、S4の `_run(..., site=...)`、S5の `decide(..., site=...)` を正規 seam とします。これは DW-O14 [operations:74–77](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/dev-wave/operations.md:74) に沿います。

dispatcherは command runner・clock・sleepを keyword-onlyで注入し、fake qsub/qstatが marker・result・logsを作る形にします。実qsubはunit testで呼びません。

## 段5の実装単位

| Unit | 所有ファイル |
|---|---|
| U1 先行 | 新規 `orchestrator/campaign/site_policy.py`、新規 `orchestrator/tests/test_site_policy.py` |
| U2 | `tools/run_tests.py`、新規 `tools/pegasus/dispatch.py`、`test_run_tests_nproc.py`、`test_run_tests_preflight.py`、`test_run_tests_task_run.py`、`test_pegasus_tools.py` |
| U3 条件付き | `buildcache.py`、coverage 4 modules、`test_buildcache_v2.py`、新規 `test_build_jobs_policy.py` |
| U4 | `hooks/guard_bash.py`、`test_hooks.py` |
| 親 | S6 docsのみ |

編集所有は素集合です。U1の API と定数を先に固定し、所有path限定patchを U2/U3/U4へ配布します。U2は `collect_receipt.py` の既存private helperをimportするだけで編集しません。public化が必要と親が判断した場合のみ、同ファイルをU2所有へ追加します。

現在のblockingによりU3は投入不可です。wave全体のbrief整合を守るなら、U2/U4も先行実装せず親裁定後に段5を開始します。

## brief への反論

blocking反論はS4です。推奨裁定は、briefの不変条件を次へ狭めることです。

> 既存凍結bytes、cache identity、contract identityは変えない。今後生成する実行manifestの `build_argv` は実際の affinity由来 `-j N` を正直に記録してよい。

この改訂なら既存凍結成果物を編集せず、S4を正直なprovenance付きで実装できます。現不変条件を維持する場合はS4をscopeから外すしかなく、「Pegasus計算ノードでbuildを最大並列」という依頼を満たせません。

S5については、`guard_bash` 単独でscript file・変数展開・Codex tool面まで完全強制するのは技術的に不可能です。S2とS4を一次gate、S5を明示tokenの第二防壁と解釈すれば成立します。

静的検査のみで、pytest・qsub・cmakeはいずれも実走していません。したがって緑の報告はありません。