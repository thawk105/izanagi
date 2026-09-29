# [T-2489] A-2 認証を 5 ノードで 1 attempt 実走した — 50 分が 12 分 08 秒になった。ただし 2 request は共有 home の bench.lock で今も直列化している

**種別: 実行基盤の実機測定 (判断材料)。** D1910 項 2 が「実測が揃うまで裁定しない」と置いた
「A-2 (rr5 / rr50) の `scheduler.nodes` を 5 にするか」について、A-2 固有の 5 ノード実走 1 本を取り、
出力同値性・所要短縮・queue 費用を現行 (nodes=1) の attempt と並べる。**恒久採用の裁定は本稿では
下さない。** A-2 の科学的結論 (採用版の効果) も更新しない。付随して出た性能値は §7 に書くが
A-2 の主張には使わない。

- 日付: 2026-09-18 (投入 06:45:49 JST、両 request 終了 06:58:31 JST)
- wave: `worktree-dev-wave-t2489-a2-nodes5-probe` (local main `d2ebef7a4` から、wave branch の実装面差分ゼロ)
- 実走した source commit: `3f61c3408` — main tip `d2ebef7a4` に「A-2 policy の `scheduler.nodes` 1→5」の
  1 行だけを足した**使い捨て commit** (branch `probe/t2489-a2-nodes5-submit`、main / wave branch へ入れない)
- 一次資料: `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2489-20260918a/`
  (attempt root。`collect` は行っていないので repo 内に成果物は無い)
- 比較対象 (現行 nodes=1): 同 base の attempt `t2364-20260907b` (2026-09-07、source `31ec382a7`、
  repo 内成果物 `output/insights/2026-09-07_t2364-paper-story-a2-certification/`)
- 統治する裁定: D1910 項 2 (実測後に索引へ戻す)、D1810 (fan-out 機構)

## 0. 何が分かったか

1. **A-2 の 2 request (rr5 / rr50) は nodes=5 で完走し、所要は 680 s / 728 s (11 分 20 秒 / 12 分 08 秒)。**
   現行 nodes=1 の attempt は 3020 s / 3037 s (50 分 20 秒 / 50 分 37 秒) なので、壁時計で **4.17 倍速**。
   検査 24 件 (2 workload × 2 cell × (legacy 1 + performance 5)) はすべて `serializable` / `certified` /
   anomaly 0。兄弟ノードの遠隔 result 16 件はすべて `outcome.kind = success` で、head の MAC 照合を通って
   WAL へ取り込まれた。driver_rc は両方 0。
2. **現行 A-2 の 50 分は、検査の直列 5 本だけでは説明できない。rr5 と rr50 の 2 request が別ノードで走り
   ながら `~/.izanagi/bench.lock` を奪い合って、performance 検査 pass と bench を cluster 越しに
   直列化している** (§3)。`orchestrator/campaign/lock.py:default_lock_path` は `IZANAGI_BENCH_LOCK`
   未設定なら `~/.izanagi/bench.lock` を使い、A-2 / A-6 の job body はこの変数を設定しない
   (`tools/pegasus/b10_backoff_grid.sh` と `a5_second_boot_backoff_sweep.sh` は `$TMPDIR/bench.lock` へ
   逃がしている)。`/home` は Lustre で `rw,flock` mount (login node の `/proc/mounts` 実測)。
   **WAL に lock の取得・解放は記録されないので、これは「時刻が秒単位で整合する強い推測」であり
   立証ではない** (§3 に別説明の余地も書く)。
3. **nodes=5 でも 2 head は同じ lock で直列化したままである。** 5 ノード走の WAL と fan-out task の
   作成時刻は、rr5 の head が rr50 の pass 終了を待ってから task を作った (2 cell とも) ことを示す。
   直列化区間が「5 本の直列検査」から「rep 0 と兄弟 4 本の並列検査」に縮んだので、待ちも縮んだ。
4. **node 秒は増える。** 5 × 680 + 5 × 728 = 7040 node 秒 (1.96 node 時間) 対 3020 + 3037 = 6057 node 秒
   (1.68 node 時間)、+16.2 %。兄弟 4 ノードが働いた時間は 2300 node 秒で、予約された兄弟 node 秒
   5632 の 41 %。予約上限は walltime 6 時間 × 10 ノード = 60 node 時間 (policy 不変)。
5. **queue 待ちは 87 s と 18 s** (5 ノード割当、06:45 JST、gen_S は 139 JSV 中 RUN 18 / QUE 8)。
   現行 attempt の 1 ノード割当は 119 s / 117 s (2026-09-07 21:10 JST)。1 標本ずつであり、混雑時の
   待ちは測っていない。
6. **`protocol_sha256` は nodes を変えても不変** (`scheduler` は preimage 外)。現行 main の A-2 policy
   (nodes=1) と probe (nodes=5) の両方で `d99f08bc…7f9c` を実測。ただし現行 attempt `t2364-20260907b`
   の `136b823e…d9f4` とは**異なる**。差は 09-07 以後の main 側 policy 改版 (T-2198 `934fe9af1`、`trace0_cmake_argv` へ FetchContent 引数 prefix を追加) によるもので、nodes とは無関係。

## 1. 投入の形

| 項目 | 値 |
|---|---|
| policy | `orchestrator/campaign/paper_story_a2_certification.v2.json` の `scheduler.nodes` を 5 にした使い捨て commit `3f61c3408` (bytes sha256 `f8a77806…472c`、他は不変) |
| 投入元 | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-a2-nodes5-probe/submit-tree` (git worktree、branch `probe/t2489-a2-nodes5-submit`、`git worktree lock` 済み) |
| 投入 | `tools/pegasus/submit_paper_story_a2_certification.sh --policy orchestrator/campaign/paper_story_a2_certification.v2.json --attempt-id t2489-20260918a --ccbench-root <tree>/external/ccbench --dependency-prefix-source /work/1/SFC/tanab/izanagi-a2-deps --third-party-source-root <tree>/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` (rc=0、06:45:35〜06:45:59 JST) |
| qsub argv | `-A SFC -q gen_S -b 5 -l elapstim_req=06:00:00 -N paper-a2-cert` (両 workload、submission receipt の逐語) |
| job body | `tools/pegasus/paper_story_a2_certification.sh` (sha256 `2a3205cf…d70`、A-6 と同一 file、rank>0 gate 込み) |
| CCBench pin | `511c953` |
| 終了後 | `finish-group` で `receipts/completion.json` と `receipts/acquisition.json` を書いた (rc=0)。`collect` は行わない |

rank>0 の 4 job は job body の gate で即終了した (両 request の `job.stderr` に
`nonzero PBS job number exits without running compute body` が 4 行ずつ)。

## 2. 所要と費用 — 現行 attempt との対比

### request ごと (NQSV 会計 `job.stderr` の逐語値)

| attempt | workload | request | nodes | Created → Started (queue 待ち) | Started → Ended | Elapse | 割当 |
|---|---|---|---:|---|---|---:|---|
| t2364-20260907b (現行) | rr5 | 981476.nqsv | 1 | 21:10:08 → 21:12:07 (119 s) | 21:12:07 → 22:02:23 | 3020 s | bnode002 |
| t2364-20260907b (現行) | rr50 | 981477.nqsv | 1 | 21:10:10 → 21:12:07 (117 s) | 21:12:07 → 22:02:40 | 3037 s | (1 ノード) |
| **t2489-20260918a** | rr5 | 4978.nqsv | 5 | 06:45:49 → 06:47:16 (87 s) | 06:47:16 → 06:58:31 | **680 s** | bnode110, 112, 113, 114, 115 |
| **t2489-20260918a** | rr50 | 4979.nqsv | 5 | 06:45:53 → 06:46:11 (18 s) | 06:46:11 → 06:58:15 | **728 s** | bnode106, 116, 117, 123, 124 |

- attempt 全体 (最初の Created → 最後の Ended): 現行 3152 s (52 分 32 秒)、本走 762 s (12 分 42 秒)。
- job 内の campaign 外 (staging・条件 gate・後始末): 現行 57 s / 57 s、本走 51 s / 47 s。変わらない。
- **費用 Σ nodes × Elapse**: 現行 6057 node 秒、本走 7040 node 秒 (+983、+16.2 %)。
- 兄弟ノードの実働: rr5 4 × (116 + 122) = 952、rr50 4 × (165 + 172) = 1348、計 2300 node 秒
  (task.json 作成から result.json 書込までの mtime 差)。兄弟の予約 4 × (680 + 728) = 5632 node 秒に対し 41 %。
  残りは head の build・legacy 検査・lock 待ち・bench の間の遊休。
- 予約上限 (walltime): 現行 2 × 6 h = 12 node 時間、本走 10 × 6 h = 60 node 時間。hang すればここまで課金される。

### cell ごとの工程 (campaign WAL の時刻差、本走)

`+` は直前の WAL 行からの秒数。「lock 待ち」は WAL に無い値で、**兄弟 task.json の作成 mtime** (pass の
lock 取得後に作られる) と相手 request の pass 終了時刻から読んだ推定である。

| request | cell | build | legacy | lock 待ち → task 作成 | rep 0 (head) | 兄弟 4 本 (task → result) | 兄弟取込 | bench (待ち + 実体) |
|---|---|---:|---:|---|---:|---|---:|---|
| rr50 | stock `960e57e1aeba` | 17.7 | 16.7 | 0 → 06:47:28 | 157.1 | 160〜165 s | +8.4 | 133.0 (= rr5 pass 終了まで 116 + 16.8) |
| rr5 | stock `960e57e1aeba` | 17.3 | 16.9 | **97.6** → 06:50:14 | ≈114 | 113〜116 s | +2.1 | 33.7 (= rr50 bench まで 17 + 16.8) |
| rr50 | adopted `c48efb21ee4b` | 17.6 | 12.8 | 0 → 06:53:00 | 161.1 | 167〜172 s | +11.9 | 141.8 (= rr5 pass 終了まで 125 + 16.9) |
| rr5 | adopted `ecad154a2cbf` | 15.1 | 13.4 | **158.3** → 06:55:53 | ≈125 | 121〜122 s | +0.1 | 33.7 (= rr50 bench まで 17 + 16.8) |

campaign 本体は rr5 629.4 s、rr50 680.6 s。`bench_wall_s` は 4 cell とも 16.8〜16.9 s。

現行 attempt (nodes=1) の同じ表は `evidence/analysis-t2364-20260907b.txt` にある。要点: rr5 の performance
検査は 5 本 × 110〜120 s、rr50 は rep 0 が 722〜746 s (うち約 560〜580 s が lock 待ち)・rep 1〜4 が
155〜168 s。rr5 は最後の検査から bench まで 804〜850 s (うち約 787〜833 s が lock 待ち)。

### 所要短縮の帰属

並列化分と lock 待ち短縮分は**独立に足せない**。2 request が 1 本の lock で直列化している限り、壁時計は
「cell ごとの排他区間の鎖」でほぼ決まる。

| 構成 | cell あたりの排他鎖 (rr50 pass + rr5 pass + bench 2 本) | 2 cell + build/legacy/job 外 | 実測 |
|---|---|---|---|
| nodes=1 (現行) | ≈ 800 + 560 + 34 = 1394 s | ≈ 2940 s | 3020 / 3037 s |
| nodes=5 (本走) | ≈ 165 + 116 + 34 = 315 s | ≈ 700 s | 680 / 728 s |

鎖が 4.4 倍縮み、全体は 4.17 倍縮んだ。**検査 pass が 5 本の直列から「rep 0 + 兄弟 4 本の並列」へ
変わったことが、自 request の pass 短縮と相手 request の待ち短縮の両方を生んでいる。**

### 静的見積り (未実測、仮定付き)

lock を node-local (`IZANAGI_BENCH_LOCK=$TMPDIR/bench.lock`、b10 / a5 の job body と同形) にした場合の
見積り。仮定 = rep 時間は本走・現行のまま、2 request は同時開始、overhead は小。**本 wave では測っていない。**

| 構成 | rr5 | rr50 | 壁時計 (遅い方) | node 秒 |
|---|---|---|---|---|
| nodes=1 + node-local lock | ≈ 2963 − 1620 ≈ 1340 s | ≈ 2980 − 1173 ≈ 1810 s | **≈ 30〜31 分** | ≈ 3260 (job 外 57 s × 2 込み、現行の約半分) |
| nodes=5 + node-local lock | ≈ 629 − 290 ≈ 340 s | ≈ 681 − 241 ≈ 440 s | **≈ 8 分** (+ job 外 50 s) | ≈ 4400 (job 外 ≈ 50 s × 2 込み) |

現行の 50 分のうち約 20 分は、追加ノード無しで lock の置き場だけで消える計算になる。これは job body
の変更 (scope 外) を要するので、裁定パッケージ (§9) へ添える。

## 3. bench.lock の cluster 越し直列化 — 証拠と読み方の上限

### 機構 (file:line、現行 main `d2ebef7a4`)

- `orchestrator/campaign/lock.py:24-34` `default_lock_path`: `IZANAGI_BENCH_LOCK` が無ければ
  `~/.izanagi/bench.lock`。`bench_lock()` は同 path への `fcntl.flock(LOCK_EX)`。
- `orchestrator/campaign/pipeline.py:2393-2428`: performance 検査 pass (`fullscale_isolated`) は
  `with bench_lock():` の中で競合 probe → `_run_fanout_pass` / `_run_one_pass` を回す。fan-out 時も
  **head は兄弟の future 完了と取込まで lock を保持する** (`pipeline.py:2289-2322`)。
- `orchestrator/campaign/pipeline.py:1386`: bench も `with bench_lock():`。
- `tools/pegasus/paper_story_a2_certification.sh`: `IZANAGI_BENCH_LOCK` を設定しない
  (`export` は `IZANAGI_RESERVATION_*` と `PYTHONDONTWRITEBYTECODE` のみ)。
- 兄弟側 worker は `task_root/bench.lock` (node-local、task 単位) を使う
  (`orchestrator/campaign/verify_fanout_worker.py:470-535`)。
- login node の `/proc/mounts`: `/home` と `/work` はどちらも `lustre rw,flock,…`。計算ノード側の
  mount option は本 wave で読んでいない (推測)。

### 時刻の整合 (本走、秒単位)

| 事象 | 時刻 (JST) | 読み |
|---|---|---|
| rr50 cell 1 legacy 検査完了 → task.json 作成 | 06:47:28.6 → 06:47:28 | lock 空き、即取得 |
| rr5 cell 1 legacy 検査完了 | 06:48:36.5 | ここから lock 待ち |
| rr50 cell 1 pass 終了 (兄弟 4 本取込) | 06:50:14.1 | lock 解放 |
| **rr5 cell 1 task.json 作成** | **06:50:14** | 解放と同秒に取得 (待ち 97.6 s) |
| rr5 cell 1 pass 終了 | 06:52:10.3 | lock 解放 |
| rr50 cell 1 bench_done (`bench_wall_s` 16.8) | 06:52:27.1 | 解放 + 16.8 s = 06:52:27.1 ✓ |
| rr5 cell 1 bench_done | 06:52:44.0 | rr50 bench 終了 + 16.8 s = 06:52:43.9 ✓ |
| rr50 cell 2 legacy 完了 → task 作成 | 06:53:00.1 → 06:53:00 | 即取得 |
| rr5 cell 2 legacy 完了 | 06:53:14.8 | lock 待ち |
| rr50 cell 2 pass 終了 | 06:55:53.1 | 解放 |
| **rr5 cell 2 task.json 作成** | **06:55:53** | 同秒に取得 (待ち 158.3 s) |
| rr5 cell 2 pass 終了 | 06:57:58.0 | 解放 |
| rr50 cell 2 bench_done | 06:58:14.9 | 解放 + 16.9 s ✓ |
| rr5 cell 2 bench_done | 06:58:31.7 | rr50 bench 終了 + 16.8 s ✓ |

現行 attempt `t2364-20260907b` と `t2228-20260904a` も同型に整合する (`evidence/baseline-wal-timelines.txt`)。
例: t2364 cell 1 は rr5 pass 終了 21:23:35.6 → rr50 rep 0 完了 21:26:16 (+161 s = rep 1 本分)、
rr50 pass 終了 21:36:42.4 → rr5 bench_done 21:36:59.4 (+17 s = bench 1 本分)。

### 上限

- WAL に lock の取得・解放は無い。task.json の作成 mtime は lock 取得**後**の事象だが、取得の瞬間
  そのものではない。「相手の解放と同秒」が 2 cell × 3 attempt で繰り返すことが根拠であり、
  I/O 遅延・page cache・trace flush が同じ対応を偶然作る説明は弱いが WAL だけでは排除できない
  (段 3 相談の指摘)。
- 直接立証するなら、2 ノードから同じ lock file を flock する probe か、`bench_lock()` の取得・解放を
  WAL へ出す変更が要る。どちらも本 wave の scope 外。

## 4. 出力の同値性 — 科学的条件の同値と成果物の対応

### 一致したもの (科学的条件)

| 項目 | 現行 t2364-20260907b | 本走 t2489-20260918a |
|---|---|---|
| bench の argv (`run_cmd`) | `ycsb_silo.exe -thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=2100 -ycsb_zipf_skew=0.9 -ycsb_rratio={5,50} -ycsb_rmw=0 -ycsb_max_ope=10` | 同一 (4 cell とも逐語一致) |
| 性能 reps / 検査 reps | 5 / legacy 1 + performance 5 | 同一 |
| stock genome / variant | `BACKOFF_FIXED=-1, BACK_OFF=0` / `960e57e1aeba` | 同一 |
| adopted genome | rr5 `BACKOFF_FIXED=10, BACK_OFF=1`、rr50 `BACKOFF_FIXED=5, BACK_OFF=1` | 同一の genome 文字列 |
| CCBench pin | `511c953` | 同一 |
| workload の順序 | stock → adopted | 同一 |
| WAL の stage 列 (cell ごと) | build_start, build_done, verify_done × 6, bench_done, commit | 同一 (verify_done 6 本の内訳が「head 5 本」から「head 1 + 兄弟 4」に変わる) |

### 成果物の対応 (本走)

- 検査 24 件: すべて `verdict=serializable` / `certified=true` / `anomalies=0`。
- 遠隔 result 16 件 (`verify-fanout/<variant>/performance-{1..4}/result.json`): すべて `outcome.kind=success`、
  `rep` 1〜4、`result_mac` あり、`remote_verification_receipt.lock_identity_sha256` は各 campaign lock と一致
  (rr5 `d13c1136…`、rr50 `94973334…`)。**MAC は head が実行時に照合して受理した証拠であり、事後に独立
  再検証したものではない** (secret は永続化されない)。
- WAL の verify_done は cell ごとに legacy → rep 0 → 兄弟 4 本の順 (positional evidence、rep 番号は
  result.json 側)。
- `compute-result.json` は両 workload とも `driver_rc: 0`、`pbs_jobid` は `0:4978.nqsv` / `0:4979.nqsv`。

### 一致しないもの (同値性の対象外、ただし明記)

| 項目 | 現行 | 本走 | 意味 |
|---|---|---|---|
| `protocol_sha256` | `136b823e…d9f4` | `d99f08bc…7f9c` | 09-07 以後の main 側 policy 改版 (T-2198 `934fe9af1`) による。**nodes=1 / 5 の間では不変** (§0-6) |
| policy bytes sha256 | (当時の main) | `f8a77806…472c` | nodes を含むので変わる (A-6 と同型) |
| job body sha256 | `b23eed2c…ab0` | `2a3205cf…d70` | 09-07 以後の job body 改版 (rank gate 等) |
| source_commit | `31ec382a7` | `3f61c3408` (使い捨て) | 当然異なる |
| adopted cell の variant ID / source bytes | rr5 `1f2762881fcb`、rr50 `47e599584695` | rr5 `ecad154a2cbf`、rr50 `c48efb21ee4b` | **patch bytes が変わっている** (`tracked_diff_sha256` `b7b4c79a…` → `29aef2bc…`、adopted の `source_bytes_sha256` も変化。stock の source bytes は不変)。原因は本 wave で追っていない。adopted の性能値を attempt 間で比べるときは同一 source でない |

## 5. 実機経路 — A-6 (T-2457) との差分だけ

- 2 request が同時に走る形は A-6 (1 workload) には無かった。durable root は `jobs/rr5` / `jobs/rr50` で
  分離され、campaign・cache・receipts の衝突は無い (段 3 相談の静的確認と、本走で両方 rc=0)。
- write-heavy (rr5、abort 1800 万/rep) と balanced (rr50、commit 420 万/rep) の full-scale trace を
  兄弟ノードの `/scr` で完走させた。容量・メモリの余裕は測っていない (完走した事実だけ)。
- 兄弟 4 本は head の rep 0 と**同時に**走っている: task 作成から result 書込までが 113〜172 s で、
  head の rep 0 (114〜161 s) とほぼ同じ長さ。5 本を直列に回す 570〜830 s との差が並列の証拠。
- 兄弟取込の overhead (rep 0 完了から 4 本の取込完了まで) は +0.1〜+11.9 s。

## 6. 主張の上限

1. **1 attempt・2 workload・各 2 cell の 1 回きり。** 混雑時の queue 待ち、`/scr` の容量余裕、
   node-local lock にしたときの実所要は測っていない。
2. lock 直列化は §3 のとおり強い推測。
3. 兄弟ノードの実 hostname は成功 result に無い (A-6 と同じ)。head は割当一覧の先頭
   (rr5 bnode110、rr50 bnode106) と推定している。
4. `collect` していないので、本 attempt は A-2 の certification として公開されていない。
   `tracked_destination` は現行 attempt の leaf のまま。
5. 使い捨て commit `3f61c3408` は submit-tree の branch にだけ在る。テストの policy sha256 pin
   (`orchestrator/tests/test_paper_story_a2_certification.py`) は動かしていないので、この commit を
   そのまま main に載せることはできない (policy を変えるなら別 wave、pin 閉包込み)。
6. adopted cell の patch bytes が 09-07 と異なる (§4)。本稿は性能を比較しないので結論に影響しないが、
   attempt 間で性能を比べる者への注意として残す。

## 7. 付随して得られた性能値 — A-2 の判定には使わない

| workload | cell | median tps (本走) | CV | median tps (現行 t2364) |
|---|---|---:|---:|---:|
| rr5 | stock | 2,431,955 | 4.0 % | 2,438,295 |
| rr5 | adopted (`BACKOFF_FIXED=10`) | 3,965,640 | 1.3 % | 3,987,794 |
| rr50 | stock | 3,698,142 | 3.1 % | 3,756,230 |
| rr50 | adopted (`BACKOFF_FIXED=5`) | 4,269,761 | 1.0 % | 4,297,929 |

性能計測は fan-out の対象外で head だけで走り、検査がすべて終わってから始まる。adopted の source bytes は
現行 attempt と異なる (§4)。この値で A-2 の判定を更新しない。

## 8. 工程と工数

- 段 1 brief → 段 3 相談 1 本 (read-only、`gpt-6-astra` / medium、11 所見 must-fix 9 / nit 2、全採用) →
  段 4 裁定 → 段 5 author 1 本 (submit-tree の 1 key 編集のみ) → 投入・待ち・finish-group → 記録。
  段 6 レビュー子は省略 (軽量版、wave branch の実装面差分ゼロ)。変異 matrix は免除 (DW-S04)。
- 逐語: `verbatim/s1-brief.md`、`verbatim/s3-consult.md`、`verbatim/s4-ruling.md`、`verbatim/s5-author.md`。
  `s3-consult.md` は whitespace 検査に抵触する行末空白 3 行 (総括の 101〜103 行目、Markdown の行末 2 space) を
  可逆最小正規化で除去した (可視文字不変)。原文 sha256 `e47ecf399d8d1818c30caed67ad563fe80cb4a898e6bdadd5df63b766503cbbf`
  (13080 bytes) → 正規化後 `f1b59e895cf482aaed12bd4db4a95f93191e98032abced11ba951f707ff6dab6` (13074 bytes)。
  復元法: 当該 3 行の行末に space 2 個を戻す。原文は wave job dir の `s3-consult.md`。
- 解析の射影: `evidence/analysis-t2489-20260918a.txt`、`evidence/analysis-t2364-20260907b.txt`、
  `evidence/baseline-wal-timelines.txt`、`evidence/qstat-state-transitions.txt`。解析 script は wave job dir
  (`analyze_attempt.py`、`wal_timeline.py`、`read_receipts.py`、`protocol_sha.py`)、repo へは入れない。

## 9. 裁定パッケージ (索引へ戻す)

いずれも本稿では決めない。

1. **A-2 policy の `scheduler.nodes` を 5 にするか。** 実測: 壁時計 50 分 → 12 分 08 秒 (4.17 倍)、
   node 秒 +16 %、queue 待ちは 1 標本で悪化せず、検査 24 件・遠隔 16 件すべて受理。採るなら別 wave で
   policy 1 key + テストの sha256 pin 更新 + 波及閉包 (A-6 の T-2429 と同形)。
2. **A-2 / A-6 の job body で `IZANAGI_BENCH_LOCK` を node-local (`$TMPDIR/bench.lock`) にするか。**
   b10 / a5 の job body には前例がある。静的見積り: nodes=1 のままでも 50 分 → 約 30 分、nodes=5 なら
   約 8 分。lock は「同一マシン内の bench 排他」が設計意図 (`lock.py` docstring) で、別ノード間の排他は
   意図された保護ではない (推測)。採るなら実測 1 本で確かめる。
3. **遠隔実行に walltime より短い総 timeout を入れるか** (T-2457 §9 の再掲。今回も予約上限は 60 node 時間)。

## 10. 再現条件

| 項目 | 値 |
|---|---|
| 投入元 | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-a2-nodes5-probe/submit-tree` (HEAD `3f61c3408`) |
| 投入 | §1 の command、attempt `t2489-20260918a` |
| 生値 | `<attempt root>/jobs/{rr5,rr50}/raw/`、WAL は `jobs/<w>/campaigns/<campaign>/runs/wal.jsonl` |
| fan-out 証拠 | `jobs/<w>/campaigns/<campaign>/verify-fanout/<variant>/performance-{1..4}/{task,result}.json` |
| 受領証 | `<attempt root>/receipts/{submission,completion,acquisition}.json` |
| 外からの採取 | wave job dir の `qstat-samples.log` (30 秒間隔の `qstat -f`、両 request) |
| 段 3 相談・裁定・author | wave job dir と本 insight の `verbatim/` |

## 所在の移動・撤去 (2026-09-30 追記)

本 insight が投入元として名指す submit-tree `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-a2-nodes5-probe/submit-tree` と branch `probe/t2489-a2-nodes5-submit` (使い捨て commit `3f61c3408`) は、2026-09-30 の掃除 wave で回収せずに撤去する。commit `3f61c3408` は branch 束 bundle `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/backup/branches.bundle` から復元できる。
判定の根拠・木ごとの退避の所在・残る写しの一覧は `output/insights/2026-09-30/cleanup-originals-migration/README.md` を正本とする。上の本文は当時の事実として書き換えない (記録された測定・判定は撤去を理由に無効にならない、規律 7)。撤去は同 wave の land の後に行う。
