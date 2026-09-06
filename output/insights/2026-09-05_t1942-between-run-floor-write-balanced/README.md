# [T-1942] 走行間ばらつきの下限 (between-run noise floor) を write-heavy と balanced について Pegasus 計算ノードで測った

- 日付: 2026-09-05 (JST)
- wave: `dev-wave-t1942-between-run-floor-wl` (branch `worktree-dev-wave-t1942-between-run-floor-wl`)
- 裁定: D1638 (実施主体 = AI)、D1639 (依頼が指す量 = 走行間ばらつきの下限。B-4 §5 の floor へ流用しない。official 床値 [T-2324] を待たない)
- driver: `orchestrator/campaign/between_run_floor.py` (無変更。commit 97ee3cd3a の blob)
- 結論: **2 workload とも測定に成功した。** 成果物は `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.{json,md}` と同 `_rr50_rmw0.{json,md}` (driver の create-only 出力をそのまま複写)。

---

## 1. 結果 (論文の環境節に使う数値)

構成: records 1,000,000 / threads 48 / extime 3 s / clocks_per_us 2100 / stock silo
(`silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`) / trace-disabled build / perf 無し。
within = 10 反復 × 1 セッション。between = 独立 8 セッション (各 5 反復の median) の session-median の変動係数。

| workload | rratio | abort 率 | within CV | within median (tps) | between CV | between median (tps) | node | request |
|---|---:|---:|---:|---:|---:|---:|---|---|
| write-heavy | 5 | 79% | 2.70% | 2,319,730 | **0.95%** | 2,280,352 | bnode073 | 978588.nqsv |
| balanced | 50 | 68% | 1.18% | 3,834,563 | **0.73%** | 3,796,356 | bnode100 | 978589.nqsv |
| read-heavy (既測、commit e5a0dba4c) | 95 | 15% | 1.00% | 10,242,274 | 0.22% | 10,152,112 | bnode040 | 934445.nqsv (2026-08-22) |

session_throughputs (between の 8 値):

- write-heavy: 2,309,998 / 2,291,591 / 2,308,657 / 2,255,593 / 2,295,093 / 2,269,114 / 2,259,516 / 2,268,248
- balanced: 3,834,702 / 3,839,047 / 3,798,924 / 3,761,214 / 3,807,086 / 3,772,259 / 3,793,789 / 3,784,963

旧環境 (linux-baremetal、D19 の実測) との並記:

| workload | 旧環境 within | 旧環境 between | Pegasus within | Pegasus between |
|---|---:|---:|---:|---:|
| write-heavy | 2.19% | 0.67% | 2.70% | 0.95% |
| balanced | 1.07% | 1.07% | 1.18% | 0.73% |
| read-heavy (旧環境は 2026-07-11 実測) | 0.19% | 0.11% | 1.00% | 0.22% |

旧環境の値は `output/env/linux-baremetal/calibration/between_run_noise_t48_*.json` から取った (abort 率は 82% / 70% / 16%)。

読み方: (1) 3 workload とも between < within で、driver の docstring どおり「back-to-back の独立セッションは
cold-boot / 温度ドリフトを含まない**下限**」である。(2) abort 率が高いほど between CV が大きい
(15% → 0.22%、68% → 0.73%、79% → 0.95%)。(3) A-1 pilot の 3% 床値 (D19 / D1640) は Pegasus の
between CV 最大値 0.95% の約 3 倍にあたる。**この値を B-4 §5 の `floor` 欄へ流用してはならない** (D1639)。

## 2. 何をどう測ったか (投入経路)

read-heavy の既測 (2026-08-22、wave t1477、job 934445) と同じ経路を段 1 で実測して写した。

- 使い捨ての PBS job body + login submitter (repo 非昇格)。現物は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1942-between-run-floor-wl/scripts/`
  (`between_run_floor_point.pbs` sha256 `a2dd3bb812e7ee5ee15447f0a93dea0884c0629d4576edd6c36cbd59f8a5885c`、
  `submit_between_run_floor_point.sh` sha256 `36ed26c76af0ff80a264aedbc029ea16d3e245ea52e1c31e44d51dd752303830`)。
  Codex `role=author` が先例 (`dev-wave-t1477-d58-ablation/dev-wave-scratch-final/`) から計測段だけを残して書いた。
- `qsub -l elapstim_req=01:00:00 -o <repo外> -e <repo外> -v IZANAGI_REPO_ROOT=…,IZANAGI_BETWEEN_RUN_ENV_TAG=pegasus,IZANAGI_FLOOR_POINT=<point>,… <pbs>`。
- job body: `/scr/<jobid>` を TMPDIR、python3.10 shim、node identity、site compiler (gcc 11.4.0)、
  `tools/pegasus/policy.json` の pin で gflags / glog を static build して `CMAKE_PREFIX_PATH`、
  `pgrep -af 'ycsb_.*\.exe'` (競合 bench 0 件 = rc 1)、`python3 orchestrator/campaign/between_run_floor.py <point>`、
  JSON 契約検査 (schema / workload / cv / records / threads / clocks)、binary sha256、manifest。
- **2 workload は別 checkout (detached submit-tree、commit 97ee3cd3a、submodule 初期化済み) から別ノードへ同時投入した。**
  同じ checkout から同時に build すると `buildcache.build` の publish が衝突しうる (`buildcache.py` の
  「legacy publish 先が build 中に出現したため上書きしない」) ため。build cache は tree ごとに空から fresh build した。
- 所要 (job の Elapse): write-heavy 232 s (calibration 215 s)、balanced 245 s (calibration 221 s)。
  投入 20:31、開始 20:32、終了 20:36 JST。queue は gen_S QUE 140 / RUN 33 だったが待ちは 1 分未満だった。

一次資料 (repo 外、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1942-between-run-floor-wl/`):

- `pegasus-run/write-heavy/manifest.json`、`pegasus-run/write-heavy/job-1788607907079620596-1169425/` (calibration.stdout、node-*、compiler-*、gflags-*、glog-*、competing-bench.*、calibration-binaries.json、calibration-output/)
- `pegasus-run/balanced/manifest.json`、`pegasus-run/balanced/job-1788607913579011535-1171032/` (同上)
- `pegasus-run/<point>/submissions/<nonce>/` (submit-receipt.json、qsub-command.txt、qstat_Q / pegasusinfo の preflight)
- scheduler stdout/stderr: `pegasus-run/<point>/scheduler-<nonce>.{stdout,stderr}`

binary (trace-disabled、driver が `trace=False` で build、`_assert_no_trace_symbols` を通過):

- write-heavy: `submit-tree-write-heavy/external/ccbench/build-variants/silo_0b3832a454_t0/cc/silo/ycsb_silo.exe` sha256 `bd769d93cfb8c27e96dbcdf4d8d1a79461e3187e24edd89ed3ef475c7e4d4c34`
- balanced: `submit-tree-balanced/external/ccbench/build-variants/silo_155bb9df86_t0/cc/silo/ycsb_silo.exe` sha256 `ee6f36c5fe57254328d0dc706e6b934e71ff211c66de48e9e81dc422ae2b8b20`
- 2 本の sha256 が異なるのは build root path が別 (cache key と debug prefix が tree ごと) のため。同じ source (CCBench pin 511c9538、同 genome) から同じ compiler で build した。

## 3. read-heavy 既測の provenance (段 1 で確定した事実)

committed の `between_run_noise_t48_skew0p9_rr95_rmw0.json` (commit e5a0dba4c、2026-08-22 20:57) は、
worklog 864 が引く job 934086 (bnode014、between CV 0.2174%) の出力**ではなく**、その後の job 934445
(bnode040、2026-08-22 20:18:54 開始、calibration 199 s、between CV 0.2228%、within 1.00%、median 10,152,112) の出力である。
一次資料は `/work/1/SFC/tanab/dev-wave-t1477-pegasus-run/job-1787397268715679073-4173218/calibration.stdout`。
同日の 3 走行 (934086 / 934347 / 934445) の between CV は 0.22% / 0.14% / 0.22% で、read-heavy の走行間ばらつきの下限は 0.1〜0.2% 台にある。

## 4. 検査 (段 6、軽量版。review 子は起動していない)

実装面は repo 外の使い捨て script 2 本だけで、repo tracked file の実装面差分は 0。変異 matrix の代わりに
DW-M01 の事前登録どおり親が login node で次を実測した (`checks/m1_result.txt`、`checks/m2_result.txt`)。

| # | 検査 | 正例 | 負例 |
|---|---|---|---|
| M1 | job body の JSON 契約検査 `validate_floor_json` (逐語切り出し) | rr95 JSON を期待 95 で rc 0 | rr95 JSON を期待 5 / 50 で rc 1 (`workload: False` だけが偽) |
| M2 | 出力既存時の create-only preflight (逐語写し) | 不在の rr5 で rc 0 | 既存の rr95 で rc 2 |
| 正例 | 実 job 2 本 | 両方 status success、契約検査通過 | — |

そのほか: `bash -n` 2 file、埋め込み Python の ast.parse、submitter `--dry-run` 2 point (実 `qstat -Q` で gen_S ENA ACT)、
投入直後の `qstat` 可視性、manifest の source commit / script sha256 が submitter の値と一致。

## 5. 何をしていないか

- driver・gate・台帳・test を変えていない。B-4 §5 の floor 欄に触れていない。official 床値 campaign を起動していない。
- 段 2・3 (codex plan / consult) と段 6 の敵対レビュー子は軽量版として省いた (設計択一なし・正しさ防壁に触れない・受理集合不変)。
- push していない。

## 6. 子の構成

- 段 5 Codex `role=author` 1 本 (job script + submitter)。prompt は job dir `prompts/stage5-author.md`、出力 `logs/stage5-author-output.md`。
- 計測 job 2 本 (PBS、gen_S、01:00:00)。
