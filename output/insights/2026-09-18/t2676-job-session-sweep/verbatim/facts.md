# 親が実測した事実 (段 1、2026-09-18)

## F-1 job 内 dispatcher は session leader ではない
T-2675 request `4026.nqsv` (bnode028、条件 keep) の `.e` file:
- dispatcher (`--job-run`) の trace pid = **3010049** (`supervisor-wait-start` 〜 `job-run-returned`)。
- 隔離 supervisor (unshare → python bootstrap) の pid = 3010056、直接の子 (probe) の pid = 3010070。
- probe が記録した自分の `sid` = `pgid` = **3010029**、`ppid` = 3010056。
- よって **dispatcher は session leader ではない** (pid ≠ sid)。session leader 3010029 とその配下がどの process で、いま生きているか、dispatcher の祖先かは
  **未採取** (段 3 B-5 で訂正)。「自分以外を全部 kill」する走査は leader が同 uid なら殺しうるので、祖先鎖の除外と ns 帰属述語 (段 4 裁定 A-1) を置く。
- 逐語: `t2675-request4026-dispatcher-trace.txt`。

## F-2 孤児化した残存子の ppid は 1
T-2622 insight §6.3: 「子の `ppid` は親の終了後 `1` へ変わる (孤児化) が、`sid` は job のまま」。subreaper は鎖に無い (F973 で撤去済み)。
残存 process の直接の親は死んでいるので `pgrep -P` や子孫走査では拾えない。session 走査は今回採る経路 (唯一とは言わない、D1002 の path 帰属もある)。

## F-3 現行 job body の構造 (worktree `tools/pegasus/dispatch_compute.py`、HEAD d2ebef7a4)
- `_job_run` :1530〜1711。child 段は :1647〜1674 (`stage = "child"` :1647、`_run_bound_tests_child` または `_run_isolated_child`)。
  except 連鎖 :1675〜1682、isolation 失敗は :1685〜1687 で `INFRA_RC` を即 return。result 書込み `_write_result_replace` :1704、`job-return` trace :1709。
- 入れ子 user ns: `_run_isolated_child` は `/usr/bin/unshare --user --map-root-user --mount` (:1112〜1116) で bootstrap を起動し、bootstrap の子は
  さらに `unshare(CLONE_NEWUSER)` (:293) してから `execvpe` する。**全 task の子孫は dispatcher と異なる user ns に居る。** dispatcher 自身は init ns。
- login 実測 (`probe_ns_attribution.out.txt`、2026-09-18 06:50): 同 uid の入れ子 ns 孤児について、外から `readlink /proc/<pid>/ns/user` が読めて
  (`user:[4026537420]` ≠ 自分 `user:[4026531837]`)、`uid_map` も読め (`31609 31609 1` vs 自分 `0 0 4294967295`)、`os.pidfd_open` →
  `signal.pidfd_send_signal(SIGTERM)` → `select.poll` で 0.8 ms 後に POLLIN、`/proc/<pid>` 不在、その後の `pidfd_send_signal(0)` は ESRCH。kernel 5.15。
- `_run_isolated_child` :1080〜1197: `Popen` (:1131) に `start_new_session` 指定なし。`process.communicate` で supervisor だけを待つ。
- bootstrap `_ISOLATED_CHILD_BOOTSTRAP` :214〜337: `os.fork()` (:282) → 子は inner userns → `execvpe` (:304)、親は正の pid で `waitpid` (:328)。
- job script `_job_script` :834〜913: `export IZANAGI_DISPATCH_REQUEST_SHA256="$REQUEST_SHA256"` (:911) の後、`exec "$selected" "$DISPATCHER" --job-run "$REQUEST"` (:913)。
- `_is_bound_job_envelope` :1500〜1528 は script を substring 照合 (`REQUEST=`, `REQUEST_SHA256=`, `export IZANAGI_DISPATCH_REQUEST_SHA256=`, `exec ... --job-run "$REQUEST"`)。行の追加では壊れない。
- child_env の pop 列 :1620〜1627 (`_TASK_RUN_ENV`, `_TASK_RUN_ROOT_ENV`, `_REQUEST_SHA256_ENV`, sidecar/auto-record)。
- `_job_trace` :710〜718: `IZANAGI_DISPATCH_JOB_TRACE` + JSON を stderr へ。**consumer は dispatch_compute.py 自身以外に 0 件** (tools/ orchestrator/ hooks/ を grep)。
- `main` :4485〜4501: `--job-run` は 2 または 3 引数。`_job_run` の後に `job-run-returned` を出す。
- TASKS の env_mode: tests / provenance = **inherit**、mutation / generic = clean (:113〜162)。

## F-4 `_job_run` を login node の pytest 内で in-process に呼ぶ既存テスト
`orchestrator/tests/test_pegasus_dispatch_compute.py`:
- :1134〜1149 `test_job_run_passes_sidecar_and_auto_off_to_tests_child` → `_job_run_with_mocked_child` (:4083〜4157、`_run_isolated_child` を mock)。
- :2421〜2422 `mock.patch.object(DC, "_run_isolated_child", return_value=0)` の下で `DC._job_run(request)`。
- :4199〜4205 `_actual_job_run` — 実 `_run_isolated_child` を login で走らせる (unshare 実走)。呼び手 :4265 / :4337 / :4375 / :4398 (bootstrap を `raise SystemExit(0)` に patch)。
- :6186 `DC.main(["--job-run", str(request), request_sha256])`、:6210 `DC.main(["--job-run", str(request)])` — いずれも `mock.patch.dict(DC.os.environ, {...}, clear=True)` の下。
無条件の session 走査を `_job_run` に入れると、これらのテストは **pytest worker 自身の session (xdist の兄弟 worker、受入 runner、その祖先) を走査対象にする**。
opt-in は仮想リスク向けの gate ではなく、この実在経路を塞ぐための発火条件。

## F-5 pin と重複
- `tools/pegasus/dispatch_compute.py` の bytes pin は無し (admission_registry は path key + class `local-ok`、`check_docs.py` は TASKS 表の乖離検査のみ)。
- main より先の全 branch でこの file を変更するものは 0 件 (164 worktree、2026-09-18 06:20)。

## F-6 再利用する器具
- T-2675 probe `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2675-nqsv-run-membership/probe_t2675_run_membership.py` (sha256 f781162298f8885bd8d73f9e5d65d0d763fa14cc7e1673dd9961d42f9dc5b3e1、30,373 bytes)。
  `--condition keep` = 親 5 秒で終了・子 75 秒 (所属不変、fd 1/2 保持、5 秒周期 heartbeat、SIGTERM handler 無し = 既定動作で終了)。`--condition no-child` = 統制。
  投入形は前 wave の `run-probe.sh` (generic、`--walltime 00:03:00 --queue-wait-timeout 1800 --overall-grace 2100 --accounting-grace 120 --poll-interval 2`)。
- 前 2 wave の同器具で `E − J`: keep 69.5 秒、no-child −0.001 秒 (D2124)。
