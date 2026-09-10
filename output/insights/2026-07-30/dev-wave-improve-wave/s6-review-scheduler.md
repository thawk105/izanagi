結論は **NO-GO**。静的レビューだけで Critical 7件、High 5件を確認した。pytest/build/qsub は実行しておらず、green は一切主張しない。

`integrated.patch` と `git diff --cached --binary` は同一 SHA-256 `94e548...234d`。staged 32 path のうち実装・テスト・設定21 pathは各U1〜U4 worktreeのbytesと一致し、integration独自の実装hunkはなかった。ただし所有境界違反が1件ある。

## 所見

### F1 — Critical / REAL — `policy.json` が凍結所有外

- 場所: [plan-v2.md:80](/home/SFC/tanab/.codex/dev-wave-improve-wave/s6-review-scheduler/plan-v2.md:80)、[author-u2.md:9](/home/SFC/tanab/.codex/dev-wave-improve-wave/s6-review-scheduler/author-u2.md:9)、[policy.json:22](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/policy.json:22)
- 攻撃入力: U2が所有一覧にない `tools/pegasus/policy.json` のaccount/queue/walltime/timeout/quotaを変更する。
- 成果物影響: live qsubの資源・取消・snapshot上限が未裁定author bytesで決まる。全実装hunkが「所有patch由来」という条件は不成立。
- 最小fix: `policy.json` の所有を再裁定し、正規ownerによる実装・integrationをやり直す。事後追認だけでは不可。
- 期待赤node: 新設 `stage6::implementation_owner_closure[tools/pegasus/policy.json]`。

### F2 — Critical / REAL — manifestが実行bytesを束縛しない

- 場所: [test_dispatch.py:1043](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1043)、[test_dispatch.py:1131](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1131)、[submit_tests.py:126](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/submit_tests.py:126)
- 攻撃入力: manifest作成後、worker開始前にsnapshot内のtest、`run_tests.py`、`submit_tests.py`を置換する。workerはmanifest自身とroot pathしか再検証しない。
- 成果物影響: final receiptはmanifest hashを持つが、実際に実行したtest/runner bytesは別物になり得る。「何をtestしたか」の証明が偽になる。
- 最小fix: executable/test closureのpath・mode・symlink・SHA-256 inventoryをmanifestへ入れ、worker開始直前とrunner終了時に再計算してresult/finalまで連鎖する。
- 期待赤node: `test_worker_rejects_snapshot_tree_drift_after_manifest`。

同じ欠陥により、[submit_tests.py:201](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/submit_tests.py:201) はtracked job scriptが外部へのsymlinkでも `.resolve()` した外部pathを、[test_dispatch.py:1733](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1733) は無検査でqsubへ渡す。`run_tests_job.sh -> /tmp/evil.sh` を拒否する `test_qsub_rejects_job_script_symlink_escape` も必要。

### F3 — High / REAL — local Git configがqsub前にコード実行できる

- 場所: [test_dispatch.py:470](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:470)、[test_dispatch.py:485](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:485)、[test_dispatch.py:701](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:701)
- 攻撃入力: source `.git/config` に `core.fsmonitor=/tmp/payload` を設定する。または `.git/info/attributes` とfilter/textconv設定を注入する。
- 成果物影響: snapshot/preflightのread-only想定Git操作がlogin node上で任意副作用を起こせる。checkout変換によりsourceとsnapshotの実行bytesも不一致になり得る。
- 最小fix: local configを信頼しないGit plumbing経路へ限定し、少なくともfsmonitor/filter/textconvを明示無効化する。`.git/info/attributes`も検査し、tracked bytesを直接hashする。
- 期待赤node: `test_snapshot_rejects_local_fsmonitor_and_info_attributes`。

### F4 — High / REAL — size/quota/log上限が総量を制限しない

- 場所: [test_dispatch.py:625](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:625)、[test_dispatch.py:727](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:727)、[policy.json:40](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/policy.json:40)
- 攻撃入力: tracked、Git objects、main untracked、ignored fixture、各submodule untrackedを、それぞれ2 GiB未満にする。tracked単一fileは128 MiB超でも通る。pytestは30分間stdout/stderrを無制限に出す。
- 成果物影響: 各カテゴリが別々に上限判定されるため合計がfree-spaceを超え、共有filesystem上の既存成果物生成まで阻害する。失敗したpartial snapshotと過去dispatchも蓄積する。
- 最小fix: 全カテゴリ・Git objects・既存dispatchを含むprojected aggregateを一回で判定し、全regular fileにper-file上限を適用する。copy後再検査、partial cleanup/retention、spool上限も必要。
- 期待赤node: `test_snapshot_quota_is_aggregate_across_all_categories`、`test_tracked_file_obeys_max_file_bytes`。

### F5 — Critical / REAL — NQSV accountingをqstat成功と取り違える

- 場所: [test_dispatch.py:1599](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1599)、[test_dispatch.py:1609](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1609)、既存正本 [silo_ladder_rung1.py:3662](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/silo_ladder_rung1.py:3662)
- 攻撃入力: valid runner-result、空または`stderr\n`だけのspool、任意内容の`qstat -f` rc=0。
- 成果物影響: Request ID、Started/Ended Request Time、Elapseがないのに`CHILD_RESULT`成功となる。実在fixtureでもaccountingはNQSV stderr epilogueにあり、qstat出力ではない。
- 最小fix: stderrのサイズ安定を待ち、既存 `validate_nqsv_accounting_epilogue()` 相当でexact job IDと必須fieldを検査する。raw stderrと抽出accountingをfinalへhash束縛する。
- 期待赤node: 現在の [test_monitor_ordered_trace_keeps_transient_qstat_distinct:260](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_test_dispatch.py:260) は、`stderr\n`だけで成功するため修正時に赤になるべき。加えて `test_monitor_rejects_missing_or_wrong_nqsv_accounting_footer`。

### F6 — Critical / REAL — scheduler状態機械が早期成功または無期限待機する

- 場所: [test_dispatch.py:1500](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1500)、[test_dispatch.py:1574](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1574)、[test_dispatch.py:1577](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1577)、[test_dispatch.py:1251](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1251)
- 攻撃入力:
  - Running後にrunner-resultが見え、qstatが1回だけrc=1、その後再びRunning rc=0。
  - Queued/Held/Pre-runningを各timeout未満で往復。
  - 未知state文字列。
- 成果物影響: runner-result存在時はtransient limitを無視して即disappearedとなり、F5と組み合わさるとjob継続中に成功finalを出せる。phase遷移ごとにtimerがresetされるためcontrollerは無期限に残り得る。未知stateはqueuedへ倒される。
- 最小fix: result有無とtransient判定を分離し、exact state allowlist、回復可能poll、qsubからの絶対deadlineを設ける。deadline到達時はqdelと終端receiptを必須にする。
- 期待赤node: `test_transient_after_runner_result_recovers_running`、`test_state_flapping_hits_global_deadline_and_qdel`、`test_unknown_qstat_state_fails_closed`。

### F7 — Critical / REAL — qsub受理後のorphan window

- 場所: [test_dispatch.py:64](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:64)、[test_dispatch.py:1803](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1803)、[test_dispatch.py:1847](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1847)、[test_dispatch.py:1859](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1859)
- 攻撃入力:
  - schedulerは受理したがlocal qsubがtimeoutする。
  - valid job ID取得後、`qsub.stdout`またはsubmit receipt書込みがENOSPC。
  - qsub後、monitor開始前または実行中にSIGTERM。
- 成果物影響: timeoutはrc127→`SUBMIT_FAILED`となり、既に存在するjobを追跡・取消できない。receipt書込みとsignalの窓もqdelされず、bounded resource契約を破る。
- 最小fix: qsub呼出し直前から終端まで一つの補償状態機械にする。timeoutは`SUBMIT_UNKNOWN`としてunique job nameで照合し、既知ID取得後の全例外・signalはqdelする。resumeはWALから照合し、自動再qsubしない。
- 期待赤node: `test_qsub_timeout_after_acceptance_is_submit_unknown`、`test_receipt_write_failure_after_job_id_qdels`、`test_sigterm_after_submit_qdels_once`。

### F8 — Critical / REAL — 不完全finalと不正rcを成功へ倒せる

- 場所: [test_dispatch.py:1871](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1871)、[test_dispatch.py:1976](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1976)、[test_dispatch.py:1347](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1347)
- 攻撃入力: canonical JSON `{"controller_exit_status":0}` をfinal pathに置く。またはrunner-resultへ`runner_exit_status=-15`を置く。
- 成果物影響: resumeはschema、dispatch ID、manifest/auth/submit/log/accounting chainなしで0を返す。負rcはfinalで`-15`だが外側のPython process statusは241となり、controller/child/OS rcが一致しない。
- 最小fix: outcome別のexact final schema validatorを一元化し、全hash chainとstatus domainを検査する。signalは`signal=15`と正規化rc=143のように明示する。
- 期待赤node: `test_resume_rejects_incomplete_final_status_zero`、`test_negative_child_status_is_normalized_and_bound`。

### F9 — High / REAL — qsub argv/envとjournalがprovenance chain外

- 場所: [test_dispatch.py:1782](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1782)、[test_dispatch.py:1798](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1798)、[test_dispatch.py:222](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:222)
- 攻撃入力: policy load後にsnapshot内policyを変える、または完了後にJSONL journalを書き換える。
- 成果物影響: journalには再計算不能なargv hashだけがあり、raw argv、policy hash、job-script hash、qsub stdout/stderr/rcはfinalへ連鎖しない。account/queue/walltime/export envを後から証明できない。
- 最小fix: qsub前にexact `qsub-request.json` をcreate-only作成し、raw argv/env、policy/job-script/manifest hashesを入れる。そのhashをauthorization→submit→finalへ連鎖し、journalもprev-hash chainにする。
- 期待赤node: `test_final_binds_exact_qsub_request_policy_and_job_script`、`test_journal_hash_chain_detects_rewrite`。

### F10 — Critical / REAL — canonical `pegasus_policy`をshadowできる

- 場所: [buildcache.py:27](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:27)、[s3_lock_coverage.py:37](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s3_lock_coverage.py:37)、[test_campaign.py:419](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_campaign.py:419)
- 攻撃入力: `orchestrator/pegasus_policy.py`を置く、または偽`pegasus_policy`を`sys.modules`へpreloadする。coverage modulesはTOOLSの後にORCHESTRATORをindex 0へ挿すため、後者が優先される。
- 成果物影響: 偽moduleがloginをOTHERとして返せば、login-node build miss gateを迂回し、禁止されたconfigure/buildを実行できる。現テストは各callerが「同じ偽物」を共有してもidentity比較で通る。
- 最小fix: toolsを必ずindex 0へ移し、既存`sys.modules`も含めて `__file__ == <repo>/tools/pegasus_policy.py` を検証する。不一致はimport前に停止。
- 期待赤node: `test_canonical_policy_rejects_sys_path_and_sys_modules_poison`。

### F11 — High / REAL — worker環境・affinity・task-run証跡が未束縛

- 場所: [submit_tests.py:71](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/submit_tests.py:71)、[submit_tests.py:147](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/submit_tests.py:147)、[submit_tests.py:158](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/submit_tests.py:158)、[run_tests.py:804](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:804)
- 攻撃入力: `LD_PRELOAD`、`PYTHONUSERBASE`、proxy/compiler環境をjobへ残す。claim後にaffinityを変更する。task-run ID付きdispatchを実行する。
- 成果物影響:
  - workerはほぼ全環境をexecへ転送し、worker-environment receiptはrunner-result/finalにhash束縛されない。
  - claimはhostname/affinityを持たず、runnerの再観測との差を検出しない。
  - `IZANAGI_TASK_RUNS_ROOT` はallowlist外なのでtask-run eventはsnapshot内へ書かれ、canonical repository ledgerは更新されない。finalはevent IDだけでpath/hashを持たない。
  - `PIP_NO_INDEX`と文字列検査は一般network禁止を保証しない。
- 最小fix: closed env allowlist、`PYTHONNOUSERSITE=1`、固定interpreter、必要ならOS-level network isolationを使う。worker環境・hostname・affinity・distribution receipt・task-run path/hashをclaim/result/finalへ連鎖する。
- 期待赤node: `test_worker_execve_uses_closed_environment`、`test_runner_rejects_affinity_drift_after_claim`、`test_dispatch_task_run_event_is_bound_in_canonical_ledger`。

### F12 — High / REAL — fake testsが危険なmutationを殺さない

- 場所: [test_pegasus_test_dispatch.py:39](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_test_dispatch.py:39)、[test_pegasus_test_dispatch.py:66](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_test_dispatch.py:66)、[test_pegasus_test_dispatch.py:260](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_test_dispatch.py:260)、[test_pegasus_tools.py:168](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_tools.py:168)
- 攻撃入力:
  - qstat/qdelからjob IDを削除する。
  - noncanonical runner-resultを許可する。
  - accounting footer検査を削除する。
  - env scrub/network対策をno-opにし、文字列だけ残す。
- 成果物影響: FakeSchedulerはargv prefixしか比較せず、FakeFilesystemはraw JSON bytesを通さない。現monitor fixtureは偽accountingを成功として固定化し、network testはsource文字列検索だけ。unsafe live branchをacceptanceが見逃す。
- 最小fix: exact argv/timeout比較、実file bytesと `_load_exact_json()` を通すfixture、実NQSV stderr footer、submit後例外/signal、submodule/ignored/size/post-manifest tamperをbranch-levelで検査する。
- 期待赤node: mutation `drop_qstat_job_id`、`bypass_canonical_json`、`accept_qstat_as_accounting`、`remove_worker_env_scrub` の全て。

## 静的に反証できた攻撃

以下は該当箇所を静的に確認しただけで、green判定ではない。

- U1のknown login/compute/OTHER、未知NQSV、Pegasus類似host、bnode+PBS欠落、compute affinity全数、OTHER cap32、explicit `-n0` は [pegasus_policy.py:191](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus_policy.py:191) と [pegasus_policy.py:286](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus_policy.py:286) では計画どおり。
- exact wrapper `--help`/`--version`、raw argv、login早期dispatch、compute authorization、各preflight/xdist early returnのrunner-resultは [run_tests.py:859](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:859)、[run_tests.py:958](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:958)、[run_tests.py:1007](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:1007) では正しい順序。
- cached patchの`--index`、unstaged worktree適用、source外argv拒否、untracked/ignoredのmode/hash/symlink検査、remote除去・alternates拒否、unique create-only dispatch directoryは実装されている。ただしF2〜F4を塞がない。
- genuine canonical policyを使う限り、buildcacheはvalid hitを先に返し、missだけloginで拒否する。[buildcache.py:646](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:646)
- qlogin markerless受理、system-wide floor、v3 provenanceは実装したふりをしていない。bnode+PBS欠落はfail-closed、build `-j16` とv2は維持されている。

## 総括

**NO-GO**。

must-fixは次のとおり。

1. `policy.json` の所有境界を再裁定する。
2. snapshot実行closure、job script、policy、qsub argv/envをexact hash chainへ入れ、worker開始時に再検証する。
3. NQSV stderr accounting、qstat transient/global deadline、unknown stateを正す。
4. qsub受理後の全例外・timeout・signal・resumeをorphan不能な状態機械にする。
5. final/runner rcのexact schemaとstatus正本を設け、不完全receiptの成功化を止める。
6. canonical import shadow、Git local config副作用、aggregate quota、open worker environmentを塞ぐ。
7. 上記mutationを実branchで赤にするtestへ置き換える。

現状のbytesをlive qsubへ投入する根拠はない。
