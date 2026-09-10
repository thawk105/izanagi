結論は **NO-GO** です。`integrated.patch` と staged diff は SHA-256 `94e548…34d` で一致しました。以下は統合後 bytes の静的レビュー結果です。pytest / build / qsub は実走しておらず、green は主張しません。

## 所見

### F1 — provenance-bound `policy.json` を壊している

- severity / 判定: **BLOCKER / real**
- file:line: [policy.json:22](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/policy.json:22)、[既存成果物:41](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:41)、[既存test:1202](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1202)、[current-binding validator:3500](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/silo_ladder_rung1.py:3500)
- 再現入力: 現行 `policy.json` SHA は `497777f9…d4d7b`、HEAD と committed evidence が束縛する値は `b1c42e49…961ac`。
- 成果物影響: committed `all_pass=true` rung-1 証拠が現行 bytes へ再束縛できず、既存 test は `policy` の exact SHA 比較で決定的に赤になる。これは「additive」ではない。
- 最小fix: `test_dispatch` 設定を別ファイルへ移し、既存 `policy.json` を byte-exact に戻す。既存成果物の再発行で隠さない。
- 期待赤node: `test_silo_ladder_rung1_evidence.py::test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head`
- 所有境界: [plan-v2.md:82](/home/SFC/tanab/.codex/dev-wave-improve-wave/s6-review-contract/plan-v2.md:82) の U2 所有に `policy.json` はないが、[author-u2.md:9](/home/SFC/tanab/.codex/dev-wave-improve-wave/s6-review-contract/author-u2.md:9) は編集を明記している。

### F2 — accounting は任意の `qstat rc=0` を証拠として受理する

- severity / 判定: **BLOCKER / real**
- file:line: [test_dispatch.py:1609](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1609)、[判定:1666](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1666)、[既存test:260](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_test_dispatch.py:260)
- 再現入力: terminal poll 後、accounting poll を `rc=0, stdout="Current State = Running\n"` または空 stdout にし、valid runner-result と logs を置く。
- 成果物影響: job ID、terminal state、Started/Ended/Elapse がなくても `CHILD_RESULT` と child rc を返し、final receipt が不完全な会計を成功証拠として束縛する。
- 最小fix: accounting stdout を構造解析し、exact Request ID、normalized job ID、Ended、Started、Elapse を要求する。不完全・別job・running/queued は `ACCOUNTING_INCOMPLETE`。
- 期待赤node: `test_accounting_requires_matching_terminal_id_started_ended_and_elapse`
- 現行testの弱点: accounting fixture は `"Current State = Ended"` だけで、弱い実装を肯定している。

### F3 — OTHER 判定が既存非Pegasus環境を拒否する

- severity / 判定: **HIGH / real**
- file:line: [pegasus_policy.py:173](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus_policy.py:173)、[unknown PBS処理:227](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus_policy.py:227)、[affinity観測:252](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus_policy.py:252)
- 再現入力:
  - `classify_site("worker.example", "123.server", (0,))`
  - `sched_getaffinity` を持たない非Linux上の `observe_site()`
- 成果物影響: 無関係なPBSクラスタやmacOS等で runner は rc125、buildcache miss とcoverage helperは拒否、hookはheavy commandをfail-closedにする。brief の「非Pegasus挙動不変」「その他はOTHER」に反する。
- 最小fix: unrelated host + non-NQSV PBS は raw値を保持した OTHER とする。affinity fallback は明確にOTHERと判定できた場合だけ `os.cpu_count()` を使い、Pegasus-like hostではfallbackしない。
- 期待赤node: `test_unrelated_non_nqsv_pbs_is_other`、`test_other_observation_without_sched_getaffinity_uses_cpu_count`

### F4 — dispatch が task-run の durable root を落とす

- severity / 判定: **HIGH / real**
- file:line: [allowlist:160](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:160)、[runner env生成:676](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:676)、[worker env:158](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/submit_tests.py:158)、[runner default root:804](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:804)
- 再現入力: login側で `IZANAGI_TASK_RUN_ID=<valid>` と `IZANAGI_TASK_RUNS_ROOT=<initialized-ledger>` を設定して通常dispatch。
- 成果物影響: IDだけがhash-boundされ、rootはqsub/manifestへ渡らない。workerはsnapshot内 `output/task-runs` を選び、元のledgerにeventが残らないか、未初期化で常に `task_run_event_id=null` になる。
- 最小fix: durable output rootを入力コードとは別契約で検証・hash-bindして渡すか、worker eventをdispatch dirへ作って親が元ledgerへ一度だけ記録する。event失敗をdispatch成功源にしない規約は維持する。
- 期待赤node: `test_dispatch_preserves_durable_task_run_root_and_records_one_event`

### F5 — `s8a_trigger_freq` はsite gateより先にpin・patch・tempdirへ進む

- severity / 判定: **HIGH / real**
- file:line: [s8a_trigger_freq.py:123](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8a_trigger_freq.py:123)、[_build呼出:140](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8a_trigger_freq.py:140)、[共有helper gate:116](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8a_trigger_coverage.py:116)、[現行test:389](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_campaign.py:389)
- 再現入力: Pegasus loginで `python3 orchestrator/campaign/s8a_trigger_freq.py balanced`。
- 成果物影響: site判定前にsingle-tenant、pin検査、tempdir作成、template/instrumentation patch適用へ進む。通常例外なら復元されても、途中killではccbench dirty stateを残し得る。前段失敗がlogin拒否をmaskする。
- 最小fix: consumer `main` の先頭にsite gateを追加し、同じ観測を `_build` へ渡す。既存 `main(argv)` はkeyword-only seam追加で維持できる。
- 期待赤node: `test_s8a_frequency_login_refusal_precedes_single_tenant_pin_patch_and_tempdir`

### F6 — hook は `env -S/--split-string` で直接heavy実行を見失う

- severity / 判定: **HIGH / real**
- file:line: [guard_bash.py:210](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/hooks/guard_bash.py:210)、[heavy classifier:283](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/hooks/guard_bash.py:283)、[wrapper test:364](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_hooks.py:364)
- 再現入力: `env -S 'pytest -q'` または `env --split-string='ninja -C build'`。
- 成果物影響: parserはsplit-string payloadを単なるoption値として消費してheadなしと判断する。protected-path mentionもないためPegasus loginで許可され、pytest/buildが直接走る。
- 最小fix: `-S/--split-string` payloadを再tokenizeしてheavy classifierへ渡す。不正payloadはheavy候補としてfail-closed。
- 期待赤node: `test_bash_login_env_split_string_heavy_denied`

### F7 — 有効な `-n auto/logical` をOTHERでも先行拒否する

- severity / 判定: **MEDIUM / real**
- file:line: [run_tests.py:266](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:266)、[validator:285](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:285)、[現行spellings test:163](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_run_tests_nproc.py:163)
- 再現入力: OTHERで `python3 tools/run_tests.py -n auto orchestrator/tests/test_campaign.py`、同じく `-n logical`。
- 成果物影響: 従来pytest-xdistへ渡っていた有効形がpytest到達前にrc2となり、非Pegasus互換を壊す。
- 最小fix: OTHERではsymbolic値を保持する。computeではaffinity数へ明示解決するか、compute固有の正確な拒否に分ける。
- 期待赤node: `test_other_preserves_xdist_auto_and_logical_spellings`
- 反証済み境界: `-n0` は維持。CLIの `-n max/all` は既存xdist受理形ではなく、環境変数 `IZANAGI_TEST_NPROC=max/all` は現在も維持されている。

### F8 — safeな既存pytest入力までlogin dispatcherが拒否する

- severity / 判定: **MEDIUM / real**
- file:line: [option集合:136](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:136)、[env一律拒否:357](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:357)
- 再現入力:
  - `PYTEST_ADDOPTS=-q python3 tools/run_tests.py orchestrator/tests/test_campaign.py`
  - `python3 tools/run_tests.py -h`
- 成果物影響: executable/plugin pathを含まない既存入力でもdispatch rc125となり、help/test成果物が生成されない。`--help`/`--version` exact形だけは正常。
- 最小fix: `PYTEST_ADDOPTS` をshlex parseし、安全なliteral optionだけmanifestへ束縛する。`-h`等の既知core optionもstageする。外部plugin/path/argsfileと真のunknown option拒否は維持する。
- 期待赤node: `test_login_stages_safe_pytest_addopts_and_core_help_alias`

### F9 — worker interpreter選択がdependency-awareでない

- severity / 判定: **MEDIUM / real**
- file:line: [run_tests_job.sh:29](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/run_tests_job.sh:29)、[dependency検査:71](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/submit_tests.py:71)、[literal test:168](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_tools.py:168)
- 再現入力: PATH上で `python3.10` は>=3.10だがpytest/xdistなし、後続 `python3` は>=3.10かつ両distributionあり。
- 成果物影響: 最初のpython3.10を固定してinfra failureにし、利用可能な同一interpreter環境を不必要に捨てる。
- 最小fix: 候補ごとにversionと必要distributionをprobeし、全条件を満たす最初のinterpreterを選ぶ。
- 期待赤node: `test_worker_selects_later_python_when_first_candidate_lacks_dependencies`
- test effectiveness: 現行testはsource literalの存在だけを確認し、この分岐を実行していない。

### F10 — coverage helper gateのM18被覆がmain gateにmaskされる

- severity / 判定: **HIGH / real（test effectiveness）**
- file:line: [main拒否test:307](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_campaign.py:307)、[positive control:366](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_campaign.py:366)、[s8aだけのhelper test:389](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_campaign.py:389)
- 再現入力: s2 `_broken_build_and_verify`、s3/s5 `_build_broken` からhelper gateだけを除去またはconfigure後へ移動し、各moduleのmain gateを残す。
- 成果物影響: 現行login testはmain入口で止まり変異helperへ到達しない。compute/OTHER positive controlも `_require_direct_build_site` の復帰だけで、direct subprocessと`-j16`へ到達しない。事前登録M18の検出力を証明できない。
- 最小fix: 4 helperを直接呼ぶparameterized testを作り、loginではtempdir/applied/subprocess前拒否、compute/OTHERではmock subprocessの`-j16`まで到達させる。
- 期待赤node: `test_direct_coverage_helpers_refuse_login_before_configure[s2-s3-s5-s8a]`

### F11 — qsub resource mappingは正しいが、そのbuild gateが無効

- severity / 判定: **MEDIUM / real（test effectiveness、current implementation自体はrefuted）**
- file:line: [qsub_argv:1733](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1733)、[resource flags:1758](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1758)、[現行test:439](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_test_dispatch.py:439)
- 再現入力: `qsub_argv` の `-A/-q/-b/-l` の一つを固定値化または除去する変異。
- 成果物影響: 現行testはjob名とexportしか見ず、誤account/queue/node/walltimeでも緑になり得る。実投入では拒否、誤queue、walltime killに直結する。
- 最小fix: `DispatchPolicy` の全resource値と生成argvをexact比較する。
- 期待赤node: `test_qsub_resource_flags_match_dispatch_policy`
- PBS directive: `run_tests_job.sh` に `#PBS` はないが、標準経路はCLI flagsを正本にしており、現行値はJSONと一致する。直接qsub可能なscriptだという契約はないため、directive欠落自体は反証した。

### F12 — `test_default_jobs` は二義的かつpytest収集名

- severity / 判定: **LOW / real、nit/backlog**
- file:line: [pegasus_policy.py:286](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus_policy.py:286)、[alias:300](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus_policy.py:300)、[公開集合:330](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus_policy.py:330)
- 再現入力: test moduleで `from pegasus_policy import *`。
- 成果物影響: `test_default_workers/jobs` がpytest testとして収集され、`observation` fixture要求になり得る。また`test_default_jobs(compute)==48` はbuild jobs `-j16` と誤読できる。ただし現行production callerはないためmust-fixからは外す。
- 最小fix: `default_test_workers` 等へ改名し、`test_*` APIを公開しない。
- 期待赤node: `test_policy_exports_no_pytest_collectable_callables`

## 反証済みチェック

- buildcache v1 はvalid hitを [buildcache.py:646](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:646) で受理し、miss gateは stale clear / `_run` より前の同:661。v2もhitが同:515、miss gateが同:533、`makedirs`/claim/`_run`は後段。source/toolchain検査はread-only hit検証として先行している。静的順序上の所見は反証。
- v1 explicit `jobs` と既定`-j16`、v2/direct coverageの`-j16`はcurrent bytesで維持。cache/freeze exact keys、submodule `d706650`、protocol/selector/freeze fileへの直接hunkはない。
- Python 3.10構文、通常のcanonical `pegasus_policy` identity、既存main/helperへのkeyword-only引数追加は互換。F9のinterpreter探索だけが別問題。
- repo内relative/absolute target、caller cwd、worker側suite ID正規化、`IZANAGI_TEST_TRIGGER`、OTHERのxdist serial fallback、computeの明示 `-p xdist.plugin` はcurrent bytes上維持。
- hookの既存protected-path防壁はheavy gate後にも実行され、compute/OTHER、runner、submitter、qsub、configureの通常形は許可される。F6のsplit-stringだけが実 bypass。
- 新規testはcustom `_run` または `pytest.main` を持ち、plain-runner meta-testの字面条件は満たす。主要な手動monkeypatchもfinallyで復元される。未実走なので通過は主張しない。
- U1/U3/U4のsource ownership、親のinsight/docs追加には追加違反を確認しなかった。所有外hunkはF1のU2 `policy.json` が実所見。

## 総括

**NO-GO**。

must-fix は **F1–F11**。特に、F1の既存provenance破壊、F2の偽accounting受理、F3のOTHER互換破壊、F4のtask-run ledger脱落、F5の遅いcoverage gate、F6のhook bypassは統合不可です。F10/F11はimplementationが現在正しく見える箇所を含みますが、事前登録mutation/build gateとして検出力が不足しています。

pytest / build / qsub / live PBS は未実走であり、green結果はありません。
