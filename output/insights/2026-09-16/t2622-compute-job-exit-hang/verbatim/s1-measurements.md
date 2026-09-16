# 段 1 の実測 (逐語) — [T-2622]

## M17. 計算ノード実験・条件 A (`close-now`) の結果 (2026-09-16 11:12〜11:13)

request `559.nqsv`、submission dir `output/pegasus-dispatch/df41d55463c42332137fd06e8ca074bd/`。

- `Started Request Time: Wed Sep 16 11:12:37 2026`
- `Ended Request Time:   Wed Sep 16 11:13:52 2026`
- `Elapse: 79S`
- トレース最終事象 = `job-run-returned`、`time_ns = 1789524762268731396` → **11:12:42.269**
- **残余 (`Ended` − `J`) = 69.7 秒。** 統制 D の 0.0 秒に対して 69.7 秒開いた。
  子の寿命は `t0 + 75` 秒なので、job は**子孫の寿命いっぱいまで RUN に留まった**。

evidence (`probe-close-now.jsonl`) の逐語から読める事実:

- **job の stdout / stderr は pipe ではなく通常 file である** —
  fd 1 = `/var/opt/nec/nqsv/jsv/jobfile/0.559.10/stdout`、
  fd 2 = `/var/opt/nec/nqsv/jsv/jobfile/0.559.10/stderr`。
- 子 (pid 3996204) は `after-release` 時点で fd 1 / 2 を `/dev/null` へ差し替えた。
  この事象は `parent-exit` **より前**に出ている。つまり親が終わる前に fd を手放している。
- 子の `ppid` は `parent-exit` 後に `3996203` → **`1`** へ変わった (init へ孤児化)。
  しかし **`sid` は `3996161` のまま**で、job の session に残り続けた。
- それでも job は子の寿命いっぱい RUN に留まった。

**→ job を RUN に留める決め手は fd の保持ではなく、job の session に生きている process が
あることである。**

## M16. 計算ノード実験・統制条件 D (`no-child`) の基準 (2026-09-16 11:12)

request `558.nqsv`、bnode013、submission dir
`output/pegasus-dispatch/528caa56f7b3252c6eca1a086d72b3c8/`。

- `Started Request Time: Wed Sep 16 11:12:11 2026`
- `Ended Request Time:   Wed Sep 16 11:12:16 2026`
- `Elapse: 9S` / `Remaining Elapse: 171S` (walltime 180 秒)
- トレース最終事象 = `job-run-returned`、`time_ns = 1789524736075901683`
  → **11:12:16.076**
- **残余 (`Ended` − `J`) = 0 秒。** probe の親が `--parent-seconds 5` で終わると同時に
  job も終わる。**これが基準 J₀ である。**
- 条件 D の probe は fork しないので、job 内に残る process は無い。

親が 2026-09-16 に既存成果物だけを読んで得た値。子はこの file を一次資料として扱う
(元データは wave worktree の外にあり、子からは読めない)。

## M1. トレースの発火状況

対象 = トレース導入 commit `52e8fe7cf` (2026-09-14 07:44:44 +0900) より後に終了した
計算ノード job。走査範囲 = main checkout と全 worktree の
`output/pegasus-dispatch/*/izdw-*.e*`。

- job stderr file: **169 本**
- `IZANAGI_DISPATCH_JOB_TRACE` 行を持つ: **159 本**
- 持たない 10 本はすべて worktree `dev-wave-t2582-manifest-measurement-sources` のもので、
  同 worktree の基底が導入 commit より前 (コードが存在しない)。
- **159 本すべての最終事象が `job-run-returned`。** 他の最終事象は 0 件。

## M2. python 復帰から job 終了までの残余

`.e` file 末尾の NQSV 会計 `Ended Request Time` と、トレース `job-run-returned` の
`time_ns` の差 (秒)。

- n = 159, 最小 -1.0, 中央値 -0.4, **最大 0.0**
- 分布: `<=2s` 159 件 / `<=10s` 0 件 / `<=60s` 0 件 / `<=300s` 0 件 / `>300s` 0 件

負値は `Ended Request Time` が秒精度で切り捨てられるため。**再発は 0 件である。**

## M3. walltime 到達の有無 (全期間)

保存されている `izdw-*.e*` **338 本**全部について
`(Ended - Started) / walltime` を計算した。walltime は
`Elapse: <e>S` + `Remaining Elapse: <r>S` の和。

最大比は **0.227** (408 秒 / 1800 秒、request `888604.nqsv`)。次いで 0.199 / 0.187 / 0.180。
**walltime 近くまで走った job は 1 本もない。** F853 の実例 (request `979716`) と
F901 の実例 (`982386`) の submission dir は保存されていない。

## M4. result 公開まわりの各段の所要 (n=159)

| 区間 | 中央値 | 最大 |
|---|---|---|
| `result-file-fsync-start` → `-complete` | 19.777 ms | 315.468 ms |
| `result-dir-fsync-start` → `-complete` | 1.716 ms | **1633.431 ms** |
| `result-file-fsync-complete` → `result-published` (`os.replace`) | 0.807 ms | 2.222 ms |
| `supervisor-wait-complete` → `result-file-fsync-start` | 2.559 ms | 39.743 ms |
| `result-write-return` → `job-run-returned` | 0.027 ms | 0.042 ms |

## M5. job 実行時間の分布 (post-trace 169 本)

`Ended - Started` の実測で `<=30 秒` 120 本 / `<=120 秒` 42 本 / `<=600 秒` 7 本。
最大 227 秒。**post-trace の母集合には受入全走級の長い job が入っていない。**

## M6. dispatcher の完了判定 (コード読解)

`tools/pegasus/dispatch_compute.py` の待機ループ (関数 `_dispatch_impl` 内)。

- `qstat -f <request>` を `poll_interval_s` ごとに回し、`state == "END"` で `break`。
- `result.json` の存在はこのループの条件に入らない。成果物収集
  (`collection_deadline = clock() + accounting_grace_s`) はループを抜けた**後**。
- 期限は `total_deadline = run_observed_at + walltime_s + overall_grace_s`。
  超過で `raise DispatchError("overall-timeout")`。

したがって **job が RUN に留まり続ける限り、result.json が既に公開済みでも dispatcher は
待ち、最終的に `overall-timeout` (rc=16) になる。**

## M7. job script の構造 (逐語、submission dir の `dispatch.sh` 最終行)

```
exec "$selected" "$DISPATCHER" --job-run "$REQUEST"
```

`exec` なので job の最上位 process は dispatcher python そのものである。その前に
`cd "$REPO"` と `export PATH`、`export IZANAGI_DISPATCH_REQUEST_SHA256` がある。
`#PBS -l elapstim_req=01:00:00` などの資源指定は同 file 冒頭。

## M8. dispatcher 自身のスレッド

`tools/pegasus/dispatch_compute.py` に `threading` / `Thread` / `Executor` /
`multiprocessing` / `atexit` / `daemon` の出現は **0 件**。import は
`argparse fcntl hashlib importlib.metadata json math os re secrets shlex signal
stat subprocess sys tempfile time` と `dataclasses` `pathlib` `typing`、および
`orchestrator.scheduler_nqsv` / `orchestrator.campaign.mutation_attempt_marker`。
(なお同 file 内には isolation supervisor 用の埋め込み script があり、そこでは
`ctypes json os subprocess sys time` を import する。)

## M9. トレースの出力点 (コード読解)

`_job_trace` は `print(..., file=sys.stderr, flush=True)` で、例外は `OSError` だけ握る。
`job-run-returned` は `main()` の中で `_job_run(...)` の戻り値を受けた直後に出て、
その次の文が `return rc` である。**つまり `job-run-returned` の後に残るのは
`sys.exit()` と interpreter 終了処理、そして NQSV 側の job 終端処理だけ。**
正常終了でも hang でも `job-run-returned` が最後の行になるため、
**トレース単体では両者を区別できない。**

## M10. 既存台帳の一次記録 (逐語)

F853 の根本原因欄:

> `subprocess.run` の timeout は直接の子 (`bash`) しか kill しない。FIFO の open で block した
> 孫 (heredoc の `python3`) が job の stdout / stderr を掴んだまま残るため、pytest が終わっても
> job が終われない。負例に timeout を付けることは「test が赤になること」しか保証せず、
> 「走行が終わること」を保証しない。

F973 の事象欄 (抜粋):

> 計算ノード job が pytest 完了後に終わらない事象を直すため、
> `tools/pegasus/dispatch_compute.py` の supervisor を `prctl` で subreaper にし、
> 直接の子の終了後に残存子孫を回収する処理を入れた。実走で孫 6 本の取り残しを実際に回収できた。

## M14. generic 経路の動く先例 (逐語、段 3 投入後に追加)

`output/insights/2026-09-14/t1643-has-include-real-pair/README.md` より。

```
python3 tools/pegasus/dispatch_compute.py --task generic \
  --queue-wait-timeout 240 --overall-grace 240 --walltime 00:10:00 \
  -- python3 -B tools/t1643_has_include_pair_probe.py --output <出力先>
```

> `--walltime` は **HH:MM:SS 形式**でなければ rc=16 (setup-failure) になる。

request `997000.nqsv`、bnode009、Elapse 16S、child rc=0。
**probe は `tools/t1643_has_include_pair_probe.py` すなわち `tools/` 直下 (非 pegasus) に置かれた。**
`--task generic` の argv 検査 (`_validate_task_argv` の `generic-v1` 枝) は
「string list であること」と「先頭が非空であること」しか要求しない。

## M15. トレース corpus の task 内訳 (段 3 投入後に追加)

各 submission dir の `request.json` の `task` を集計した。

- post-trace 169 本: `tests` 132 / `provenance` 33 / `generic` 4
- 全期間 338 本: `tests` 202 / `provenance` 130 / `generic` 6
- **`mutation` task は全期間で 0 件。**

F853・F901 の症状はどちらも変異走行の文脈で起きている。ただし変異 harness の
`--runner-mode dispatch` は各試行を別 job として投げるので、その job 自体の task は
`mutation` とは限らない (`TASKS["mutation"]` は wrapper に `--runner-mode local` を要求する)。
**母集合の対応づけは未確定であり、「再発 0 件」をそのまま「症状が起きる条件でも 0 件」と
読んではならない。**

## M13. NQSV 側の終端条件についての既知事実 (段 3 投入後に追加)

`docs/pegasus-runbook.md` より。

- **per-job の cgroup による資源境界は無い** (2026-09-09 実測、request `986762.nqsv`、
  3 ノード、[T-2486])。process が入るのは per-job cgroup ではなく、node ごとに job 間で
  共有する NQSV service の cgroup (`/system.slice/nqs-jsv.service`、head は
  `/system.slice/nqs-lchd.service`)。
  → **NQSV が per-job cgroup の空判定で job 終端を決めている可能性は消える。**
- `qstat` は存在しない request に対しても rc=0 を返す。
- **終了した request は約 5〜6 秒で `qstat` から消える。** 終了後に取りに行く履歴照会 command は
  この scheduler に無い。終端の記録が要る処理は job の終了時刻に張り付いて観測する。
  → 親の poll (`--poll-interval 2`) は END か消失を 5〜6 秒の粒度で捉える。
  plan の「15 秒以上で分離」はこの粒度に対して余裕がある。
- ジョブ終了後、標準出力・標準エラーは投入時の directory へ書き戻される。

## M12. job 内の process 木 (コード読解、2026-09-16 追加)

`tools/pegasus/dispatch_compute.py` の隔離 child 起動部。

- 起動 command は
  `/usr/bin/unshare --user --map-root-user --mount -- <sys.executable> -I -c <bootstrap> <fds...> <argv...>`。
- `subprocess.Popen(command, cwd=..., env=..., stdin=PIPE または DEVNULL, shell=False,
  pass_fds=(status_write_fd, exec_write_fd))`。
  **`start_new_session` は指定されていない。`stdout` / `stderr` も指定されていない。**
  したがって supervisor とその全子孫は **job の stdout / stderr をそのまま継承し、
  dispatcher と同じ session / process group に属する**。
- bootstrap 内では `child_pid = os.fork()` の後 `os.waitpid(child_pid, 0)` で
  **直接の子だけ**を待つ。孫以下は待たない。
- `unshare` は user namespace と mount namespace だけを作り、**PID namespace は作らない**。
  よって孤児は host の init へ付け替わり、job の session には残る。
- 親側は `process.communicate(input=stdin_bytes)` で待つが、stdout/stderr が PIPE でないので
  実質 `wait()` であり、やはり直接の子だけを待つ。

job の process 木は
`dispatcher (job 最上位, exec 済み) → unshare → supervisor python → fork した子 → bash →
pytest → xdist worker …` で、**全段が job の stdout / stderr を共有する**。

## M11a. 受領証側にも症状の実例が無い (2026-09-16 追加)

保存されている `receipt.json` 全部 (main checkout + 全 worktree) を集計した。

- `"terminal_reason"` の値は **332 件すべてが `"scheduler-end-state"`**。
  `request-disappeared-after-visibility` は 0 件。
- `overall-timeout` を含む受領証は **0 件**。
- `_SignalAbort: signal 15` を含む受領証が 4 件あるが、これは dispatcher が SIGTERM で
  殺された 2026-09-15 の事故 (非 detached 起動) であって本件の症状ではない。
  同じ 4 件に `orphan-hold-release-failed` / `state-not-cancellable` /
  `fresh-qstat-gate-denied` が併記されている。

**つまり保存された全 corpus に症状の実例は 1 件も無い。** 症状の一次記録は F853 の
request `979716` と F901 の request `982386` の 2 件だけで、どちらも成果物が残っていない。

## M11. 投入経路の可用性

F853 の直後に置かれた F660 の supersede 注記 (2026-09-14、逐語):

> 本 F の射程は「新しい Pegasus 実行体を要する実測」であり、計算ノードでの実測一般ではない。
> 既登録の `tools/pegasus/dispatch_compute.py --task generic` (main 側
> `admission_registry.json` で `class=local-ok`、D895) は任意 argv を計算ノードの job 内で
> 実行するので、probe が `tools/pegasus/` 配下の新規実行体でなければ本 F に当たらず、
> 同じ wave で compute 実測を行える ([T-1643] で rc=0 を実測、request `997000.nqsv`、bnode009)。
> ただし `generic` の job は `env_mode=clean` で cwd を repo root に固定するため、
> そこでの観測は本番 admission の呼出しと探索環境まで対応づけたものにはならない。

`TASKS["generic"]` の定義 (逐語):

```
    "generic": _TaskSpec(
        child_script=("<argv>",),
        env_allowlist=frozenset(),
        probe_imports=(),
        env_mode="clean",
        argv_policy="generic-v1",
    ),
```
