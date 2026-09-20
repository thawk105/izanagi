# 運用事実 (段 1 profile probe の author / 段 2 plan / 段 3 consult 向け、親が一次資料から転記)

## 1. 未完走 2 型の一次資料 (insight `output/insights/2026-09-20/verify-phase-adopted-backoff/README.md` §5、D2160 項 4)

現行 verifier (module sha256: `core.py 4d70c244…`、`dsg.py e77eaabd…`、`parse.py 1aedb77a…`、= 本 wave の base `947fd160a` と同一) を計算ノード (Pegasus gen_S、1 node 48 core、DRAM 128 GiB、ユーザー上限約 115 GiB、per-job cgroup 無し) で `python3.10 -B -m orchestrator.verifier <trace_dir> --json --expected-commits <N> --protocol silo --ccbench-root <checkout>` (既定 worker 16) として走らせた結果 (fixed-5 候補、workload 別):

| workload | extime | commit | reads | writes | keys | edges (dedup 後) | verifier wall s | 主 process maxrss GiB | 結果 |
|---|---|---|---|---|---|---|---|---|---|
| write-heavy (rratio 5) | 3 | 2,530,609 | 1,253,524 | 23,831,828 | 989,878 | 25,081,301 | 115.7 | 9.7 | serializable |
| write-heavy | 6 | 5,017,504 | 2,485,895 | 47,250,018 | 999,703 | 50,792,622 | 247.5 | 18.8 | serializable |
| write-heavy | 10 | 8,323,838 | — | — | — | — | 3601.5 (hard timeout、SIGKILL by runner) | 17.9 | 未完走。主 process の user CPU 520 s (< 6 s 走の 817 s)、stderr 空 |
| balanced (rratio 50) | 3 | 4,450,058 | 22,050,653 | 22,142,025 | 986,828 | 62,868,744 | 166.6 | 14.0 | serializable |
| balanced | 6 | 8,855,503 | 43,875,172 | 44,065,573 | 999,548 | 127,987,677 | 357.0 | 27.8 | serializable |
| balanced | 10 | 14,748,197 | — | — | — | — | 303.1 (rc −9、runner の timeout ではない) | 21.2 | 未完走。SIGKILL、stderr 空、2 node で再現 (fixed-10 も同型: 294.9 s / 20.5 GiB) |
| read-heavy (rratio 95) | 3 | 16,819,316 | 158,318,481 | 8,406,500 | 861,206 | 291,168,798 | 416.1 | 43.2 | serializable |
| read-heavy | 6 | 32,754,846 | 308,323,065 | 16,366,030 | 965,824 | 594,786,279 | 864.3 | 85.6 | serializable (600 s 超で不適格) |

- rusage の `ru_maxrss` は主 process のみ (wait4 の rusage; worker の CPU 時間は主 process に合算されるが RSS は合算されない)。
- balanced 10 s の verify rusage: `ru_utime 772.7 s`、`ru_stime 41.2 s`、`ru_maxrss 22,185,268 KiB`、wall 303.1 s、signal 9。
- write-heavy 10 s: `ru_utime 520.2 s`、`ru_stime 26.8 s`、`ru_maxrss 17.9 GiB`、3600 s で runner が process group を SIGKILL。
- bench の argv (参考、本 wave は bench を走らせない): `ycsb_silo.exe -ycsb_tuple_num=1000000 -thread_num=48 -ycsb_zipf_skew=0.9 -ycsb_rratio=<5|50|95> -ycsb_rmw=0 -ycsb_max_ope=10 -extime=<E> -clocks_per_us=2100`、trace は 48 file (`trace_0.log` 〜 `trace_47.log`)。

## 2. 保全済み trace (入力、read-only で使う。原本は消さない・書き換えない)

- 置き場: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/run/calib/fixed-5-<workload>/extime-<e>/trace/trace_<i>.log.zst` (48 file、`zstd -T0 -3` 圧縮)。同 dir の `preservation.json` に file 別の原本 `sha256` / `bytes` / `lines` と `stored_name` / 圧縮後 sha256 がある (`files` 配列)。`result.json` の `bench.commit_witness` が `--expected-commits` の値 (balanced 10 s = 14748197、write-heavy 10 s = 8323838、read-heavy 6 s = 32754846、balanced 6 s = 8855503)。
- 圧縮後サイズ: balanced 10 s 1.3 GB (原本約 5.7 GB)、write-heavy 10 s 507 MB、read-heavy 6 s 3.0 GB (原本約 13 GB)、balanced 6 s 743 MB。復元先は計算ノードの `/scr` (NVMe 約 5.4 TB)。復元後は原本 sha256 を照合する (fail-closed)。
- `--ccbench-root` は proof surface の評価 (`assess_protocol_proof_surfaces`) が silo の source を読むために要る。本 wave の profile では submit-tree の submodule `<repo-root>/external/ccbench` (pin `511c9538`、patch なし) を渡す。verdict の値は記録するが、profile の目的は記憶量と所要であり verdict は判定に使わない。

## 3. 現行 verifier の構造 (`orchestrator/verifier/`、行番号は base `947fd160a`)

1. `parse.py` `_parse_trace_dir_compact` L787: `_effective_worker_count` (既定 min(48 file, affinity, 16) = 16) → `_parallel_file_outcomes` L627 (`multiprocessing.get_context("fork")` + `ProcessPoolExecutor(max_workers=16)`、file ごとに `_parse_file_to_columns` L547: **worker は file 全体を `Txn` object (`_parse_file` L296) に読んでから `array` 列へ詰め直し**、`_ParsedFileColumns` (token blob + array 群) を pickle で親へ返す) → `_merge_issues_and_winners` L695 (親: txid ごとの winner を dict で決め、`winner_txid` / `winner_path_index` / `winner_row` の array)。worker が 1 件でも欠ければ全部捨てて逐次 (`_sequential_file_outcomes`)。
2. `dsg.py` `DSG.from_compact` L210 → `_build_compact` L253: 親が全 write を走査して `self.producer: Dict[(key_str, (epoch, tid)), txid]` と `per_key: Dict[str, List[(epoch, tid)]]` → `self.versions[key] = sorted(set(...))`。**key は write ごとに `token_blob[...].decode("ascii")` で新しい str object**、(key, commit) の tuple も write ごと。
3. `_build_compact_edges` L290: read task (rank 範囲を read 数の重みで 16 分割) と ww task (鍵範囲) を作り、`_EdgeWorkerState(trace, producer, versions, keys)` を `initargs` にして **fork** で `ProcessPoolExecutor(max_workers=16)`。各 worker (`_edge_candidates_for_task` L110) は producer dict / versions list を **読んで** (dict lookup、bisect) 辺候補を source ごとの run (`run_src` / `run_offsets` / `run_dst` の array) で返す。全 task が揃わなければ親が逐次で全 task を計算し直す (`outcomes is None` の枝 L352)。
4. 親が `adjacency: Dict[int, Set[int]]` へ `set.update(run_dst[start:end])` で再生し (L364〜372、**set の反復順が witness を決めるので順序に敏感**、D1664)、`self.adj = {source: tuple(destinations)}`。
5. `_sccs` L429: 反復 Tarjan (dict ベース)。`anomalies` L569: SCC ごとに `_shortest_cycle` (BFS) と `_reasons` (witness の辺 type を再構成)、`max_report` 20。
6. `core.py` `verify_trace_dir` L28: 上を呼び integrity (commit witness / dup / gap / framing / lock coverage / write intent / permutation) を組み、`VerifyResult`。`report.py` `result_to_dict` が JSON。

既存の実測 (D1553、68 万 txn): 並列度 16 で所要飽和、cgroup 峰値 2.94 GB (worker 1 本 +0.08 GB)。F840: fork 子の RSS 和は CoW 共有 page を二重計上するので、記憶量は cgroup または Pss / Private_Dirty で測る。D1664 (68 万 txn): dense 配列 Tarjan (登録 pass 付き) は 3.15 → 5.65 s で遅く、鍵の大域 id (親が read を走査) は producer 構築 0.94 → 2.98 s で遅く、どちらも不採用。「登録 pass を持たない形」「writer を持つ鍵だけに id」は別 wave の候補として明記されている。

## 4. 計算ノードへの投入形 (親が行う。子は投入しない)

- `cd <submit-tree> && python3.10 tools/pegasus/dispatch_compute.py --task generic --walltime HH:MM:SS --queue-wait-timeout 14400 --overall-grace 14400 -- python3.10 -B <probe.py> run ...`。generic は clean env (`TMPDIR`・`PBS_JOBID` は渡らない)、argv を shell=False で実行。同一 worktree からの同時 dispatch は orphan hold で拒否されるので job ごとに detached submit-tree を作る。
- 計算ノード: `/usr/bin/python3.10` (3.10.12)、`zstd` あり (前 wave で使用)、`/proc/vmstat` の `oom_kill` / `pswpin` / `pswpout` / `pgmajfault`、`/proc/meminfo`、`/proc/<pid>/smaps_rollup` (Pss / Pss_Anon / Private_Dirty / Shared_Clean) は通常の権限で読める (Linux 5.15)。`dmesg` は読めない前提。
- 単独性: `orchestrator.campaign.p2_2._assert_single_tenant()` は競合 ccbench bench を検出する (verifier の競合は検出しない)。profile では加えて `/proc/loadavg` と `/proc/meminfo` の `MemAvailable` を開始時に記録し、MemAvailable が 100 GiB 未満なら測定を始めずに rc≠0 で止める (他 job の同居 = 記憶量の測定が汚れる)。

## 5. 先例 (流用可)

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-cli-timing-probe/probe/verifier_cli_timing_probe.py` (Codex author 作、544 行): `timed_process` (Popen 直前 / 復帰 / `os.wait4` 復帰の monotonic 計時、rusage、process group への SIGKILL watchdog)、`write_json`、`sha`、`file_inventory`、`selftest` の形。
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/probe/verify_phase_runner.py` (1384 行): 保全 (`zstd`) と `preservation.json` の形、`result.json` の記録項目の形。

## 6. 段 1 実測で確定した計算ノードの事実 (2026-09-20 14:00〜14:20)

- job 配下 (`dispatch_compute.py --task generic`) の子 process は **SIGTERM を無視する** (別 wave の実測 [T-2778]、`Popen.terminate()` が効かない)。`ProcessPoolExecutor` の管理 thread は壊れた pool の worker を `Process.terminate()` で殺そうとするので、計算ノードでは殺せず `join` で永久に待つ。wh10 の実測: worker 1 本の OOM kill 後、残 15 worker は state S のまま、親は `shutdown(wait=True)` から戻らない。終端には SIGKILL (`Process.kill()`) が要る。
- `/proc/vmstat` の `oom_kill` は読める。node の SwapTotal は 24 GiB だが今回の run では使われなかった。
- fork した edge worker の Private_Dirty は task 範囲でなく親の object graph に比例する (16 worker 6.1 GiB → 8 worker 8.3 GiB → 4 worker 8.9 GiB、bal10)。
