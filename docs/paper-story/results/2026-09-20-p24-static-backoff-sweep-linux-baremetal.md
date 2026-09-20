# P2-4 静的 backoff sweep の結果節 — 旧 `linux-baremetal` 環境の trace-disabled sweep 3 campaign、同一 sweep 内の無 backoff 対照との median 比 (測定 2026-06-22 / 06-28)

**これは投稿本文ではない。** 論文の結果節・表へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む。
D2120 項 15 が「paper-story の単独 results 稿は権威 bytes から作る既存経路であり、層 3 の proof chain 付き
材料レポートと同一視しない」と定める)。英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の既存の稿を改めるものではない。** results 系列にこの 3 campaign を単位とする稿はこれまで無く、
論文ストーリー 2026-09-20 版 §8 の exact claim (性能) が採る 3 値の執筆材料は、A-3 一本化 insight
(`output/insights/2026-08-25_paper-story-a3-gain-unification/README.md`。冒頭で `authority: none` を宣言する導出索引) と
`figures/README.md` の fig2b 節に散在していた。**本稿は版・claim-evidence・insight を数値の出所にせず、一次資料全体
(3 campaign の `campaign.lock`・`runs/wal.jsonl`・`reports/` の `.dat` と材料レポート、fig2b の provenance JSON、
同環境の較正記録、裁定) から作った。** 本稿の数値・日付の出所は §5 である。

**この結果は採否 protocol の出力ではない。** 3 campaign は 2026 年 6 月の Phase 2 ケーススタディ (P2-4) の sweep で、
事前登録も outer status も持たない。**論文が採る 3 値 (write-heavy +38.3% / balanced +11.3% / read-heavy −6.6%) は、
同じ sweep の中で測った無 backoff 対照 (`BACK_OFF=0`, `BACKOFF_FIXED=-1`) の 5 反復 median に対する、sweep が選んだ静的
backoff 点の 5 反復 median の比であり、有意差の判定ではなく区間推定も持たない。** 現行の対測定契約 (D496) より前の
記述的結果である (§3 限定 1)。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

**1 campaign 群 = trial `p2-backoff`、`search_tag` `sweep` の 3 campaign** (workload ごとに 1 campaign)。

| workload | campaign | `campaign.lock` の `spec_content` |
|---|---|---|
| write-heavy (rratio 5) | `backoff-sweep-silo-write-heavy-sweep-493813a7` | `P2 case study: silo static-backoff sweep — workload=write-heavy` |
| balanced (rratio 50) | `backoff-sweep-silo-balanced-sweep-484c663e` | `P2 case study: silo static-backoff sweep — workload=balanced` |
| read-heavy (rratio 95) | `backoff-sweep-silo-read-heavy-sweep-610004b9` | `P2 case study: silo static-backoff sweep — workload=read-heavy` |

各 campaign は 8 genome (無 backoff 対照・CCBench 既定の adaptive backoff・静的 backoff 6 点) を build → verify →
bench → commit の順に測り、WAL は 8 variant × 5 段階 = 40 行で、8 variant すべてが `commit` に達している (§2.5)。
**論文が採る 3 値はこの 3 campaign の WAL だけから出る。** fig2b (`figures/fig2b_backoff_sweep_3workload.{png,pdf}`) も
同じ 3 campaign を入力とするが、図の点推定は標本平均であり、論文値の出所ではない (§2.3、§3 限定 11)。

read-heavy の sweep campaign は `output/campaigns/` に 3 つあるが (`610004b9` / `6f169f90` / `8ff95955`)、fig2b の
provenance JSON が入力として指すのは `610004b9` の 1 本である。他の 2 本は A-3 insight が非正典と判定しており、本稿は
その根拠を `campaign.lock` と WAL の段階で再確認した — 両者とも `search_config` に `screening` / `screening_fixed_us` key を持ち
(`610004b9` には無い)、`ccbench_commit` は `d706650` (`6f169f90`) / `dff0f1e` (`8ff95955`) で `6656e93` ではなく、WAL は
`abort` 段階を持つ (`6f169f90` は 2 genome の bench 後に `reason: screen-slower-than-floor`、`8ff95955` は `build_start` の直後に
`reason: build-error`)。sweep の `.dat` と材料レポートはどちらにも無い (`6f169f90` の `reports/` にあるのは 2026-09-16 に
層 3 の screening 射影の回帰 pin として保存された `layer3_report.json` だけで、A-3 insight が「reports/ 無」と書いた 2026-08-25
時点より後の追加である)。**それ以上の中身は読み直していない** (§4.3)。

### 0.2 書くもの

- 3 campaign の `campaign.lock` と WAL が固定した条件 (search config、genome 8 点、CCBench commit、configure command、
  実行 argv、binary の hash、環境タグ)。
- 論文が採る 3 値と、その計算 (各側の 5 反復 median の比、A-3 insight と同じ式) の未丸め値。
- 3 campaign × 8 genome の生標本 (median、5 反復、変動係数、abort 率、IPC)。
- 図 2b の provenance JSON が持つ標本平均の `facts` と、median 比との関係。
- 当時の正しさの記録 (WAL の `verify_done`) と、その強さの限定。
- 同環境の較正記録 (records の下限基準、between-run の変動係数) — 条件としてだけ置く。
- 時系列 (WAL の epoch 秒を JST へ換算)。
- 限定 (§3) と、一次資料に無い・本稿で確かめていない箇所 (§4「欠落」)。

### 0.3 書かないもの

- 図 2b の作り直し、再測定、英語稿。
- 現行環境 (Pegasus、CCBench pin `511c953`) の 3 走行 (A-2 / A-6 / [T-1998]) や A-1・B-7・B-10 の値との集計・プール・
  横断の結論 (D1993 項 6)。符号の一致も本稿では扱わない (§3 限定 4)。
- `BACKOFF_NOINLINE=1`・`perf record` 下の機序診断 profile の値 (+38.5%) を headline として扱うこと (§3 限定 5)。
- 適応 backoff を分母にした利得 (+147.4%)、P2-2 全探索の stock 最良を分母にした値 (+39.0 / +12.9 / −7.1%)、
  別時刻の repro campaign の値 (+42.2 / +11.7%)。いずれも論文値ではなく、本稿は再計算していない (§3 限定 7・8)。
- 8 点のうち採用点以外の値から導く命題 (最適量の一般化・機序)。
- 研究としての成功・失敗・新規性の宣告 (D12)。

---

## 1. 条件 — `campaign.lock` と WAL が固定したもの

### 1.1 事前登録は無い

3 campaign に事前登録は無い。測定 (2026-06-22 / 06-28) は、性能比較を同一 campaign 内の対測定で行うと定めた
D496 (2026-08-17) より前である。反復数 (5) と集約 (median) は WAL の記録から読めるが、判定境界・反復数・集約を結果を見る前に
固定した文書は無い。実行したのは `.dat` の header が「実行再現コマンド」として名指しする driver `orchestrator/campaign/backoff_sweep.py`
(tracked) で、本稿はその当時の版を読んでいない (§4.3)。
**したがって本稿の 3 値は記述的結果であり、A-1 が定める配置と推定対象の下で測り直したものではない** (§3 限定 1)。

### 1.2 `campaign.lock` の `search_config` — 3 campaign で read 比率だけが異なる

| 項目 | write-heavy `493813a7` | balanced `484c663e` | read-heavy `610004b9` |
|---|---|---|---|
| `ccbench_commit` | `6656e93` | `6656e93` | `6656e93` |
| `trial` / `search_tag` | `p2-backoff` / `sweep` | 同左 | 同左 |
| `search_config.base` | `L-W0` | `L-W0` | `L-W0` |
| `search_config.scale` | `silo-backoff` | `silo-backoff` | `silo-backoff` |
| `search_config.workload` | `write-heavy` | `balanced` | `read-heavy` |
| `search_config.records` | 1000000 | 1000000 | 1000000 |
| `search_config.threads` | 48 | 48 | 48 |
| `search_config.sweep_us` | `[2, 5, 10, 25, 50, 100]` | 同左 | 同左 |
| `search_config.ycsb.ycsb_rratio` | `"5"` | `"50"` | `"95"` |
| `search_config.ycsb.ycsb_zipf_skew` | `"0.9"` | `"0.9"` | `"0.9"` |
| `search_config.ycsb.ycsb_rmw` | `"0"` | `"0"` | `"0"` |
| `search_config.screening` / `screening_fixed_us` | 無し | 無し | 無し |

`ccbench_commit` は短縮 token である。完全な commit は、本稿が pin 済み CCBench repository の履歴で解決した
`6656e9319566e602113edf46588de9a612d166a1` (2026-06-20 07:38:09 +0900、`Fix WAL log preallocation: 10 ^ 9 (XOR=3) -> 1000000000`)
で、A-3 insight の条件表と一致する。`campaign.lock` 自身が持つのは短縮 token までである (§4.2)。

### 1.3 genome 8 点 — WAL の `build_start.payload.genome` (3 campaign で同一文字列)

| 呼び名 | variant ID | genome (逐語) |
|---|---|---|
| **無 backoff 対照 (利得の分母)** | `84319b1127a6` | `silo\|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| CCBench 既定の adaptive backoff | `602b4ce9c788` | `silo\|BACKOFF_FIXED=-1,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| 静的 fixed 2 µs | `a6655e6b2f2e` | `silo\|BACKOFF_FIXED=2,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| 静的 fixed 5 µs | `7deff2b013e4` | `silo\|BACKOFF_FIXED=5,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| 静的 fixed 10 µs | `e44bf7ae9d29` | `silo\|BACKOFF_FIXED=10,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| 静的 fixed 25 µs | `a94f12bbaa38` | `silo\|BACKOFF_FIXED=25,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| 静的 fixed 50 µs | `3c89b874a005` | `silo\|BACKOFF_FIXED=50,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| 静的 fixed 100 µs | `610e879931c4` | `silo\|BACKOFF_FIXED=100,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |

variant ID は genome から決まる WAL の鍵であり、workload を含まない。同じ ID が 3 campaign に現れる。
静的 backoff は D18 の inert patch (`patches/silo-backoff-fixed.patch`、`.dat` の header が「ビルド再現コマンド」で名指しする)
が足した `BACKOFF_FIXED` で与える。`BACKOFF_FIXED=-1` は patch の inert 側 (静的 backoff 無効) である。
`BACK_OFF=1` かつ `BACKOFF_FIXED=-1` の genome は CCBench 内蔵の adaptive backoff であり、材料レポートは
「stock 適応 backoff (Cicada hill-climb)」と呼ぶ。**この adaptive は CCBench 既定 3 定数のもので、調整済み adaptive ではなく、
本稿の利得の分母でもない** (§3 限定 7・13)。

### 1.4 build — configure command と binary の hash (WAL の `build_done`)

無 backoff 対照の perf 側 configure command (逐語。他の 7 genome は `-DCCBENCH_BACKOFF_FIXED` / `-DCCBENCH_BACK_OFF` の値と
build directory 名だけが異なる):

```
cmake -S /home/tanab/github/izanagi/external/ccbench -B /home/tanab/github/izanagi/external/ccbench/build-variants/silo_c4c3040dca_t0 -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF -DCMAKE_C_COMPILER=gcc-13 -DCMAKE_CXX_COMPILER=g++-13 -DCCBENCH_BACKOFF_FIXED=-1 -DCCBENCH_BACK_OFF=0 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0 -DCCBENCH_TRACE=0
```

build command は `cmake --build /home/tanab/github/izanagi/external/ccbench/build-variants/silo_c4c3040dca_t0 --target ycsb_silo.exe -j 16`
(逐語。他の genome は directory 名だけが異なる)。**性能側は `-DCCBENCH_TRACE=0` の Release build
(trace-disabled) である。** `build_done` は genome ごとに `perf_bin` と `trace_bin` の 2 つの hash を持つ (規律 1 が求める
性能計測用 build と正しさ検証用 build の分離に対応する)。trace 側の configure command と、`verify_done` がどちらの binary を
使ったかは WAL に無い (§4.1)。

| genome | `trace_bin` | `perf_bin` | write-heavy での build | balanced / read-heavy での build |
|---|---|---|---|---|
| 無 backoff | `6a7c96b34c55fd16` | `60605961fe1e6925` | 新規 (`perf_cached: false`) | cache 再利用 (`perf_cached: true`) |
| adaptive | `3929fdf646d3baab` | `24c038e37efad54f` | 新規 | cache 再利用 |
| fixed 2 | `72971545a655fe1e` | `5ebe3faf765b21bc` | 新規 | cache 再利用 |
| fixed 5 | `f292a02a38897b6d` | `0e24dd80c44f4f78` | 新規 | cache 再利用 |
| fixed 10 | `8e3b74101225b41b` | `6c13c7522659c653` | 新規 | cache 再利用 |
| fixed 25 | `de182c4590befe21` | `94b8e9a4af08bdf7` | 新規 | cache 再利用 |
| fixed 50 | `77f4982f10a10ccf` | `1e1552dc3243f5d5` | cache 再利用 | cache 再利用 |
| fixed 100 | `f573154a3cf03187` | `e28f857c8af3a2bb` | 新規 | cache 再利用 |

**8 genome の binary hash は 3 campaign で同一である。** balanced と read-heavy は 8 genome とも build cache から再利用しており
(`trace_cached` / `perf_cached` がともに `true`)、write-heavy でも fixed 50 だけは再利用である。すなわち 3 workload は
同じ binary を argv (`-ycsb_rratio`) だけ変えて測っている。hash は WAL の field の 16 進 16 桁で、binary そのものは
tracked ではない (§4.2)。

### 1.5 実行 argv と測定 harness — 24 走すべて `perf stat` 下

無 backoff 対照 (write-heavy) の `bench_done.payload.run_cmd` (逐語):

```
numactl --interleave=all perf stat -e LLC-load-misses,LLC-loads,instructions,cycles -- /home/tanab/github/izanagi/external/ccbench/build-variants/silo_c4c3040dca_t0/cc/silo/ycsb_silo.exe -thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=1800 -ycsb_zipf_skew=0.9 -ycsb_rratio=5 -ycsb_rmw=0
```

3 campaign × 8 genome = 24 件の `run_cmd` は、build directory 名と `-ycsb_rratio` (5 / 50 / 95) 以外は同一である。
共通の実行条件: `-thread_num=48`、`-ycsb_tuple_num=1000000`、`-extime=3`、`-clocks_per_us=1800`、`-ycsb_zipf_skew=0.9`、
`-ycsb_rmw=0`、`numactl --interleave=all`。**24 走すべてが `perf stat` (カウンタ集計) の下で走っている。** これは
`figures/README.md` が 2026-08-26 に「後継図の系列も perf 下の測定である」と訂正した事実と同じであり、本稿はそれを WAL で
再確認した。帰結は §3 限定 6 に書く。各 genome は 1 round・5 反復 (`rounds: 1`、`tps` の要素数 5) で、`high_variance` /
`unstable` は 24 件とも `false` である。

### 1.6 較正記録 — 条件としてだけ置く

同じ環境タグ `linux-baremetal` の較正記録 (`output/env/linux-baremetal/calibration/`) は次のとおり。**本稿はこれらを
採否判定に使わない** (sweep は採否 protocol ではない。§3 限定 10)。

- **records の下限基準** — `calibration_t48_skew0p9_rr50_rmw0.json`: `saturation.records` 1000000、`saturated` false、
  `lower_bound_selected` true、`working_set_ratio` 6.637239583333334 (L3 94371840 bytes に対する倍率)、note は「miss 率が単調上昇で
  飽和点なし (masstree 系の木深化, D15)。下限基準を適用: working set (maxrss 597 MB) が L3 (90 MB) の 6.6 倍 (≥4×) になる最小
  N=1,000,000 を採用」。within-run の `noise_floor.cv` は 0.02280630204206476。同 JSON の `host` は
  `node: cygnus`、`machine: x86_64`、`cpu_count: 96`、`kernel: 5.15.0-117-generic`。
- **between-run の変動係数** (D19 の fresh 同窓測定、いずれも 8 セッション × 5 反復、genome
  `silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`):
  `between_run_noise_t48_skew0p9_rr5_rmw0.json` は `between_run.cv` 0.006662983034331659 (median 1878768.5)、
  `…_rr50_rmw0.json` は 0.010671892063164597 (median 2756157)、`…_rr95_rmw0.json` は 0.0010979692594382789 (median 8457436.5)。
  この genome 文字列は `BACKOFF_FIXED` key を含まず、sweep の無 backoff 対照 (§1.3) とは文字列が異なる。両者が同じ binary かは
  本稿で確かめていない (§4.3)。
- **採否 floor 3.0%** — D19 が定めた保守値 `BETWEEN_RUN_CV = 0.030` (`orchestrator/campaign/p2_2.py`)。3 campaign の `.dat` の
  header も `noise_floor_cv: between-run 3.0% (skew0.9, A2)` と記す。

### 1.7 環境

WAL の全 40 行 × 3 campaign が `env_tag: linux-baremetal` を持つ。campaign 側の成果物 (WAL / lock / reports) は
host 名・kernel・boot を持たない (§4.1)。同環境タグの較正記録が `host.node = cygnus` を記録し、D1525 も「元の値は cygnus で
取られている」と述べる。現行の測定環境 (Pegasus、CCBench pin `511c953`) とは機体・CCBench の版・toolchain が異なる (§3 限定 14)。

---

## 2. 結果

### 2.1 論文が採る 3 値 — 同一 sweep 内の無 backoff 対照との median 比

式は A-3 insight と同じ `100 × (variant_median / baseline_median − 1)`、表示は小数 1 桁への四捨五入。median は WAL の
`bench_done.payload.median_tps` の逐語 (各 5 反復の median)。未丸め値は本稿が同じ式で再計算し、A-3 insight の再計算表と
一致した。

| workload | 対照 (無 backoff) median tps | sweep が選んだ静的点 | その median tps | 未丸め値 | 論文値 |
|---|---:|---|---:|---:|---:|
| write-heavy | 1,882,125 | fixed 10 µs | 2,603,521 | 38.32880387859468% | **+38.3%** |
| balanced | 2,791,760 | fixed 5 µs | 3,106,342 | 11.268232226265873% | **+11.3%** |
| read-heavy | 8,450,806 | fixed 2 µs | 7,889,420 | −6.642987662951915% | **−6.6%** |

「sweep が選んだ静的点」は、6 点の静的 backoff のうち median tps が最大の点である (§2.2 の表で確認できる)。
read-heavy は 6 点すべてが対照を下回り、最大の fixed 2 µs でも対照に届かない。**3 workload の採用点は別々の量であり、
単一 treatment の一般効果として平均しない** (§3 限定 9)。

### 2.2 生標本 — 3 campaign × 8 genome

列の出所: median と 5 反復と変動係数 (cv) は WAL `bench_done.payload` の `median_tps` / `tps` / `cv`、abort 率は同
`leading_indicators.abort_rate` (逐語)、IPC は静的 6 点が `.dat` の `ipc` 列 (逐語)、無 backoff と adaptive は WAL
`leading_indicators.ipc` を小数 3 桁に丸めた値。cv は WAL の値を小数 4 桁に丸めた。latency と LLC miss 率も WAL にあるが転記しない。

**write-heavy (rratio 5)** — campaign `493813a7`

| genome | median tps | 5 反復 tps (WAL の順) | cv | abort 率 | IPC |
|---|---:|---|---:|---:|---:|
| 無 backoff 対照 | 1,882,125 | 1882125, 1881227, 1932148, 1899618, 1863575 | 0.0137 | 0.8178 | 1.997 |
| adaptive (既定) | 1,052,528 | 1037443, 1067151, 1058209, 1052528, 1041066 | 0.0116 | 0.159 | 0.426 |
| fixed 2 | 2,108,543 | 2121655, 2103867, 2108543, 2115320, 2093348 | 0.0051 | 0.7424 | 1.617 |
| fixed 5 | 2,466,887 | 2488306, 2468238, 2466751, 2466887, 2437015 | 0.0074 | 0.6219 | 1.335 |
| **fixed 10 (採用点)** | **2,603,521** | 2601441, 2645895, 2603521, 2549753, 2662903 | 0.0169 | 0.4981 | 1.08 |
| fixed 25 | 2,458,154 | 2458154, 2451998, 2402810, 2496667, 2497497 | 0.0158 | 0.337 | 0.847 |
| fixed 50 | 2,177,407 | 2191188, 2151912, 2185832, 2177407, 2155605 | 0.0082 | 0.2413 | 0.712 |
| fixed 100 | 1,814,519 | 1809838, 1818400, 1814228, 1826513, 1814519 | 0.0035 | 0.1717 | 0.59 |

**balanced (rratio 50)** — campaign `484c663e`

| genome | median tps | 5 反復 tps (WAL の順) | cv | abort 率 | IPC |
|---|---:|---|---:|---:|---:|
| 無 backoff 対照 | 2,791,760 | 2794545, 2800725, 2727244, 2773816, 2791760 | 0.0108 | 0.7036 | 1.654 |
| adaptive (既定) | 916,149 | 916149, 934742, 911267, 925661, 891309 | 0.0179 | 0.2018 | 0.383 |
| fixed 2 | 2,971,253 | 2971253, 2970346, 2959064, 3016208, 2978413 | 0.0073 | 0.6197 | 1.4 |
| **fixed 5 (採用点)** | **3,106,342** | 3133393, 3106342, 3039273, 3083210, 3112252 | 0.0116 | 0.5183 | 1.199 |
| fixed 10 | 2,899,247 | 2898865, 2899247, 2900262, 2929086, 2895834 | 0.0047 | 0.4384 | 0.991 |
| fixed 25 | 2,398,168 | 2398168, 2398867, 2400208, 2382013, 2386867 | 0.0034 | 0.332 | 0.747 |
| fixed 50 | 1,950,646 | 1956751, 1952667, 1940999, 1950646, 1950454 | 0.0030 | 0.2602 | 0.606 |
| fixed 100 | 1,522,128 | 1520630, 1514636, 1522128, 1527204, 1527330 | 0.0035 | 0.1993 | 0.493 |

**read-heavy (rratio 95)** — campaign `610004b9`

| genome | median tps | 5 反復 tps (WAL の順) | cv | abort 率 | IPC |
|---|---:|---|---:|---:|---:|
| 無 backoff 対照 | 8,450,806 | 8443409, 8450806, 8439007, 8499723, 8491002 | 0.0034 | 0.1601 | 1.683 |
| adaptive (既定) | 1,919,103 | 1927208, 1920269, 1886431, 1916584, 1919103 | 0.0083 | 0.0452 | 0.495 |
| **fixed 2 (採用点)** | **7,889,420** | 7868699, 7894996, 7880458, 7889420, 7890326 | 0.0013 | 0.1502 | 1.563 |
| fixed 5 | 7,355,208 | 7364907, 7319950, 7362758, 7355208, 7333797 | 0.0027 | 0.1412 | 1.456 |
| fixed 10 | 6,717,936 | 6703574, 6720146, 6717936, 6735607, 6691641 | 0.0025 | 0.1294 | 1.336 |
| fixed 25 | 5,568,237 | 5568237, 5570074, 5589788, 5566678, 5558095 | 0.0021 | 0.1093 | 1.115 |
| fixed 50 | 4,583,093 | 4569504, 4576289, 4583093, 4591605, 4591934 | 0.0021 | 0.0911 | 0.937 |
| fixed 100 | 3,630,211 | 3627893, 3643937, 3626918, 3631968, 3630211 | 0.0019 | 0.0726 | 0.78 |

WAL の `median_tps` は 5 反復の中央値と一致し (奇数個なので 3 番目の値)、`commit.payload.fitness_tps` も同じ値である。

### 2.3 図 2b の provenance JSON が持つ標本平均の `facts` — median 比との関係

`fig2b_backoff_sweep_3workload.provenance.json` (`izanagi-backoff-figure-provenance/v2`、`generated_utc`
2026-08-25T19:14:23.462984Z、生成器 `tools/plotting/plot_backoff.py`) の `facts` と `baselines[]` は**標本平均** (単位 M tps =
毎秒 100 万トランザクション) を持つ。

| workload | `best_bf` | `best_M` | `none_M` | `adapt_M` | `n_reps` | `baselines[0].value_tps` (無 backoff の平均) | 同 `ci95_half_tps` |
|---|---:|---:|---:|---:|---:|---:|---:|
| write-heavy | 10 | 2.6127026 | 1.8917386 | 1.0512793999999999 | 5 | 1891738.6 | 32201.049325436317 |
| balanced | 5 | 3.094894 | 2.777618 | 0.9158256 | 5 | 2777618.0 | 37101.15443512767 |
| read-heavy | 2 | 7.8847798 | 8.4647894 | 1.913919 | 5 | 8464789.4 | 35249.986074428554 |

平均から同じ式で計算すると +38.1% / +11.4% / −6.9% (本稿の再計算: 38.11118512885447% / 11.422593027550953% /
−6.852026348109752%) となり、`figures/README.md` のキャプション正文の記載と一致する。**論文値は median 比、図の点推定は
標本平均であり、両者は同じ生値の別の要約である。一方が他方の丸め違いではない** (§3 限定 11)。provenance の各入力の
`read_purpose` は `HISTORICAL_RAW`、`campaign_verifier_epoch` は `E0` (`reason_code: v1-authority-absent`) である。
図の 3 file の SHA-256 は §5.2。

### 2.4 当時の正しさの記録 — WAL の `verify_done` (verifier epoch E0)

各 campaign の各 genome について `verify_done.payload` は `verdict: serializable`、`certified: true`、`anomalies: 0` で、
24 件すべてがそうである。`commits` は次のとおり (逐語)。

| genome | write-heavy | balanced | read-heavy |
|---|---:|---:|---:|
| 無 backoff 対照 | 579044 | 575047 | 580353 |
| adaptive (既定) | 276824 | 277553 | 275270 |
| fixed 2 | 549600 | 545727 | 548511 |
| fixed 5 | 512889 | 508423 | 508224 |
| fixed 10 | 477951 | 481154 | 466152 |
| fixed 25 | 407813 | 408766 | 406173 |
| fixed 50 | 356538 | 358404 | 355831 |
| fixed 100 | 316991 | 317379 | 318230 |

**これは 2026 年 6 月の判定器による当時の判定であり、現行の certification ではない。** provenance JSON はこの campaign の
verifier epoch を `E0` (`v1-authority-absent` = 判定器の同一性を束縛する権威がまだ無かった) と記録する。verify の workload・
argv・trace file は WAL に無い (§4.1)。**論文の 3 値の正しさは、今も「backoff は正しさに影響しない」という機序論証による
外挿であり、A-2 / A-6 の certification はこの 3 値へ遡らない** (§3 限定 3)。

### 2.5 時系列 — WAL の `ts` (epoch 秒) を JST へ換算

| campaign | 最初の `build_start` | 最後の `commit` | 実行順 (variant の WAL 出現順) |
|---|---|---|---|
| write-heavy `493813a7` | 2026-06-22 22:58:59 JST | 2026-06-22 23:09:04 JST | 無 backoff → adaptive → 2 → 5 → 10 → 25 → 50 → 100 µs |
| balanced `484c663e` | 2026-06-22 23:09:04 JST | 2026-06-22 23:14:19 JST | 同上 |
| read-heavy `610004b9` | 2026-06-28 14:34:11 JST | 2026-06-28 14:39:04 JST | 同上 |

write-heavy と balanced は同日夜に連続して走り、read-heavy は 6 日後である。8 genome の binary は 3 campaign で同一 hash
(§1.4) だが、6 日の間の機体の状態 (再起動の有無・温度・周波数) は成果物に無い (§4.1)。各 campaign の WAL は
`build_start` / `build_done` / `verify_done` / `bench_done` / `commit` が 8 件ずつで、`abort` 段階は無い。

### 2.6 材料レポートの「判定」行 — 自動生成の要約であり protocol status ではない

各 campaign の `reports/backoff-sweep-<workload>_report.md` (「自動生成」と冒頭で宣言) は「判定」行を持つ:
write-heavy「静的 backoff が無 backoff を +38.3% 上回る (sweet spot あり)」、balanced「静的 backoff が無 backoff を +11.3%
上回る (sweet spot あり)」、read-heavy「静的最良でも無 backoff に届かず (-6.6%) = backoff は純損」。
**これは driver が median 比を丸めて書いた要約であり、事前登録された判定式の出力でも certification の outer status でもない。**
同レポートの参照節は無 backoff・「stock 適応 backoff (Cicada hill-climb)」・静的最良の 3 値を並べるが、利得の分母は無 backoff
だけである (§3 限定 7)。

---

## 3. 限定 — この結果が言わないこと

1. **〔但し書き 1〕D496 以前の記述的結果であって、A-1 が定める配置と推定対象の下で測り直したものではない。** 事前登録は無く
   (§1.1)、均衡 5-rep ブロック交互と AB/BA 均衡 (D1295)、D1262 の estimand、検出力から導いた n = 30 の対差平均と登録済み区間推定
   のいずれも持たない。**「同一 campaign 内の対測定が 1 件も無い」とは書かない** — D496 が求める「同じ campaign の中で比べる」
   形そのものは現行環境の 3 走行 (A-2 / A-6 / [T-1998]) が満たしている (2026-09-20 版 §8 の exact claim の但し書き 1 の
   文言による)。本稿の 3 値がそれを満たさない、というのが限定である。
2. **〔但し書き 3〕この 3 値には、計算機を別に起動し直して取り直した証拠が無い。** D1100 (2026-08-27) が論文採用の性能値を
   別 boot で取り直すと定め、D1525 (2026-09-03) が「Pegasus で取った結果は充足にならない (別の起動と別の環境が同時に変わる)」
   「A-5 は未充足のまま残す」と定めた。本稿はその未充足を明記する側であり、埋めない。
3. **この 3 値の正しさは機序論証による外挿であり、certification は遡らない。** §2.4 の `verify_done` は epoch E0 の当時の判定で、
   現行の certification (A-2 の 4 cell と A-6 の 2 cell、D1993) とは別の状態である。D1993 項 4 は「この certification は旧
   `linux-baremetal` の 3 値へは遡らない」と定める。当時の判定を新しい判定器の結果で遡って certified へ昇格させない (規律 7)。
   「正しさゲートを緩めなかった」は工程上の事実であって証明ではない。
4. **現行環境の 3 走行 (A-2 attempt `t2364-20260907b` / A-6 attempt `a6-20260908b` / [T-1998] の balanced stock-inline 対) と
   プールしない (D1993 項 6)。** 環境・CCBench の版・測定契約が違い、3 走行は互いにも protocol が別である。符号が 3 workload とも
   一致することは記述的な照合であって再現判定ではない。A-1 attempt-0001 の descriptive 出力、B-7 の同一候補 fixed 5 µs の
   3 workload 測定 (attempt `b7f5-20260919a`)、B-10 の右 tail 格子とも合算しない。旧 3 値を現行値の comparator に据えない。
5. **`BACKOFF_NOINLINE=1`・`perf record` 下の機序診断 profile が与える +38.5% を headline に使わない。理由は D20 の利用方針である。**
   D20 は「perf 下 tps は overhead 込みで headline 非使用 (絶対 throughput は stock build)」と定め、profile 自身
   (`output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.md` 末尾) も「headline throughput は stock inline build の
   値 (P2-2/backoff_sweep)。ここは spin%/IPC 比の機序分析専用」と宣言する。profile の値は無 backoff 1,867,747 → fixed 10 µs
   2,586,112 (各 3 反復の `tps_median`、本稿の再計算 38.46157964649388%) で、sweep とは (a) CCBench revision
   (`dff0f1ef2a4b84746f6463839e85b24301f4b16d`、sweep の 1 commit 後の `Fix ODR violation` 修正)、(b) 全 genome への
   `BACKOFF_NOINLINE=1`、(c) `perf record` (サンプリング) 対 `perf stat` (カウンタ集計)、(d) 3 反復対 5 反復、の 4 点で出自が違う。
   **しかしこの 4 点が利得の大きさを変えたという実証は無い** (A-3 insight: ODR 修正は `ADD_ANALYSIS=0` の build に影響しないと
   上流が明記、noinline 単体の観測者効果は D20 の実測で +0.76% = floor 3.0% の内側、利得の差 0.133 パーセントポイントは測定分解能の
   内側)。したがって **+38.5% と +38.3% を同じ測定の丸め違いとも、別 regime が効果量を変えた実証とも言わない。** 論文で機序説明に
   profile を使うときは「別 CCBench revision の noinline perf-sampling 診断では同じ公称 write-heavy contrast が 38.5% だった。
   この TPS は sampling overhead 込みで D20 により headline 値ではない」と限定を付ける (A-3 insight の「論文で使う表現」)。
6. **絶対スループット (tps) を論文の headline 値の出所にしない。** §1.5 のとおり sweep の 24 走もすべて `perf stat` 下であり、
   D20 の字義「perf 下 tps は overhead 込みで headline 非使用」は `perf record` に限定していない (`figures/README.md` の 2026-08-26
   訂正)。論文値は同じ harness の下で測った 2 側の median の**比**であり、分子と分母は同じ計装条件を共有する。D497 は
   「perf が無いことを性能主張の信頼性の条件にしない」という別方向の決定であって、perf 下の tps を headline に使ってよいとは
   定めていない。本稿は「headline 適格」という分類語を使わない。
7. **利得の分母は同一 sweep 内の無 backoff 対照 (`BACK_OFF=0`, `BACKOFF_FIXED=-1`) 1 本であり、適応 backoff ではない。** 8 genome
   に含まれる CCBench 既定の adaptive backoff (§1.3) を分母にすると write-heavy で +147.4% (本稿の再計算 147.35883510937478%) に
   なるが、これは論文値ではなく、over-throttling の大きさを示す診断値である。旧図 `fig2_backoff_mechanism.png` は無 backoff の
   値に「stock adaptive backoff」の label を付けた誤記を持つ (A-3 insight、`figures/README.md`)。本稿は「adaptive」を分母に
   書かない。また D1506 (2026-09-02) は既定 adaptive を単独の適応基準線に置いた比較から機構の優劣を言うことを禁じる。
   **既定 adaptive の 3 値 (1,052,528 / 916,149 / 1,919,103 tps) は §2.2 の記録として残すが、何の優劣も導かない。**
8. **分母の違う他の値と混ぜない。** P2-2 全探索の stock 最良を分母にした +39.0 / +12.9 / −7.1% (`output/s1-freeze/known_axes_freeze.json`
   の `p2_2_flag_opt.reference_fitness_tps`)、別時刻・逆順の repro campaign (`backoff-repro-silo-write-heavy-repro-181607af` /
   `…-balanced-repro-87dbbf50`) の no-backoff 分母による +42.2 / +11.7% は A-3 insight が「論文値ではない」参考として列挙するもので、
   本稿は再計算していない (§4.3)。repro を元 sweep と平均せず、「頑健性を定量証明した」とも言わない。
9. **3 workload の採用点 (10 / 5 / 2 µs) は別々の量であり、単一 treatment の一般効果として平均しない。** read-heavy の −6.6% を
   「backoff は常に有害」と一般化しない。機序主張は「利得は abort baseline が高いほど大きい」(A-3 insight) までであり、本稿は機序を
   主張しない。8 点のうち採用点以外の値から最適量や曲線の形の一般命題を導かない。
10. **有意差判定も区間推定も持たない。** 各側 5 反復の median の比である。D19 の採否 floor 3.0% (`BETWEEN_RUN_CV`) は当時の
    `compare` の丸め閾値であり、本稿はそれを使った採否判定を行わない (sweep は採否 protocol ではない)。§1.6 の between-run 変動係数
    (0.67% / 1.07% / 0.11%) は D19 自身が「楽観的下限」と評した fresh 同窓測定で、利得の不確かさの推定にも使わない。
11. **図 2b は論文の利得率の出所ではない。** 図の点推定は標本平均 (+38.1 / +11.4 / −6.9%)、論文値は median 比 (§2.3)。図は
    provenance の `not_certified` field と図中の `NOT CERTIFIED` 表示を持ち、variant 採用の根拠にも certified な性能結論にも
    使わない (`figures/README.md`)。図を「現行契約の測定結果」「headline 適格」と読ませない (2026-09-20 版 §7 の恒久項目)。
12. **測定日は同一ではない** (write-heavy / balanced は 2026-06-22、read-heavy は 2026-06-28)。binary は同一 hash だが (§1.4)、
    6 日の間の機体の状態は成果物に無く、3 workload を「同時期の 1 実験」と書かない。
13. **8 genome の adaptive は CCBench 既定 3 定数の adaptive backoff であり、調整済み adaptive ではない。** 3 定数の値は
    `campaign.lock` に無く、`figures/README.md` の記載 (刻み 100 µs / 上限 1000 µs / 更新間隔 10 µs) による (§4.2)。
    この 3 campaign に調整済み adaptive のセルは無く、足すには新規計測が要る。
14. **環境・CCBench の版・toolchain・計測 harness は現行と違う** (旧 `linux-baremetal` / `6656e93` / gcc-13 / `clocks_per_us` 1800 /
    `perf stat` 対 Pegasus / `511c953` / `clocks_per_us` 2100 ほか)。旧 3 値と現行値を前後比較として読まない (規律 7)。
15. **研究としての成功・失敗・新規性の宣告ではない** (D12)。§2.6 の「判定」行は driver の要約である。

---

## 4. 欠落 — 一次資料に無い箇所と、本稿で対応を確かめていない箇所

### 4.1 成果物に情報が無い

- campaign 側の成果物 (WAL / `campaign.lock` / `reports/`) に host 名・kernel・boot 識別子・CPU 周波数・温度の記録は無い。
  host の同定は較正記録 `host.node` (§1.6) と D1525 の記述による。
- compiler の exact version は無い (`-DCMAKE_C_COMPILER=gcc-13` / `g++-13` の名まで)。
- trace 側 (`trace_bin`) の configure command、verify の workload・argv・trace file・所要時間は WAL に無い。`verify_done` が持つのは
  `verdict` / `certified` / `commits` / `anomalies` の 4 field である。
- `perf stat` の生出力 (カウンタ値) は WAL に無い。残っているのは `leading_indicators` の集約値 (abort 率・latency・LLC miss 率・IPC)
  である。
- 8 genome の binary そのものは tracked ではなく、WAL の 16 進 16 桁 hash だけが残る。
- 各反復の実行時刻は無い (`ts` は段階の完了時刻)。

### 4.2 束縛の範囲が限られる

- `campaign.lock` の `ccbench_commit` は短縮 token `6656e93` までで、完全 SHA は本稿が pin 済み CCBench repository の履歴で解決した
  (§1.2)。profile 側の CCBench commit (`dff0f1ef…`) は A-3 insight が収録 commit の木から束縛した推論であり、profile artifact の
  自己申告ではない。
- 既定 adaptive の 3 定数の値は成果物に無く、`figures/README.md` の記載による (§3 限定 13)。
- `search_config.base` の `L-W0` は `.dat` の header が「no-wait-locking, WAL 無」と注記する略号で、`campaign.lock` は展開を持たない。

### 4.3 本稿で対応を再確認していない

- 非正典の read-heavy campaign 2 本 (`6f169f90` / `8ff95955`) について本稿が見たのは `campaign.lock` の key と
  `ccbench_commit`、WAL の段階と `abort` の `reason`、`reports/` の file 名までである (§0.1)。それ以外の中身と、`6f169f90` の
  `layer3_report.json` の内容は読んでいない。
- repro campaign 2 本の値 (+42.2 / +11.7%) と P2-2 stock 最良分母の値 (+39.0 / +12.9 / −7.1%)。A-3 insight の記載を参考として
  引くのみで、本稿は再計算していない (§3 限定 8)。
- between-run 較正記録の genome (`BACKOFF_FIXED` key 無し) と sweep の無 backoff 対照が同じ binary か (§1.6)。
- `reports/` の `.plt` と `.png` の内容 (本稿は `.dat` と材料レポート `.md` だけを読んだ)。
- driver `orchestrator/campaign/backoff_sweep.py` の測定当時の版 (反復数・median 集約・実行順をコードで確かめていない。
  本稿はそれらを WAL の記録から読んだ)。
- 図 2b の PNG / PDF の描画内容と provenance の対応は `orchestrator/tests/test_backoff_figure_provenance.py` と
  `test_plot_backoff_ci.py` が守る (`figures/README.md` の proof chain 節)。本稿は両テストを実行していない。

---

## 5. 一次資料

### 5.1 権威 bytes (repo 内 tracked) と SHA-256 — 本稿が 2026-09-20 に再計算した値

いずれも fig2b の provenance JSON と A-3 insight の source ledger の記載と byte 一致した。

| artifact | tracked path | SHA-256 |
|---|---|---|
| write-heavy lock | `output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/campaign.lock` | `493813a705e73908d8cbd99e55cba679f831b5cd3b8e1f40fc9f45d9dbee08ca` |
| write-heavy WAL | `output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/runs/wal.jsonl` | `9c179331a7171969ac6f4ed2b1d09e4afbf52378cfbac7bd133696a6589fe926` |
| write-heavy dat | `output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/reports/backoff-sweep-write-heavy.dat` | `5adb4c7d51188de5c4fd00842742b1d4e2f14b0efd2d2714bfe1ec5c1aedabe3` |
| write-heavy 材料レポート | `output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/reports/backoff-sweep-write-heavy_report.md` | `9590eaf5f4885ac12ab1350989076d02dbbdc607a908f156b722e53ac23ac283` |
| balanced lock | `output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/campaign.lock` | `484c663ea167ec12ac1a44b30bf15353a3b66393ac6f528dacd4d97d3f67c857` |
| balanced WAL | `output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/runs/wal.jsonl` | `8ac3f47e55274fada20e6518eea9cbb0e822170eeda1b424df99e76e11fd789c` |
| balanced dat | `output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/reports/backoff-sweep-balanced.dat` | `9ceb1b447c99abe7dcc7b50d34d44c84a6b2e4e1e4d6059ab7a317abfa0b5eb1` |
| balanced 材料レポート | `output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/reports/backoff-sweep-balanced_report.md` | `4860d2ee42dd5a703ed6c02f8d95f0a53508f57843d18e1c2c9067e429ad89a1` |
| read-heavy lock | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/campaign.lock` | `610004b9e27e2f8d6961f919b720d757e05ec6169d66ef3d5b0108c79a930c56` |
| read-heavy WAL | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/runs/wal.jsonl` | `c74d5837a4facd071704a515f905d1d638463878850661cf217b96cd694774dc` |
| read-heavy dat | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/reports/backoff-sweep-read-heavy.dat` | `49144820ec737485615209ca4b61e600a6543e4b11fa0374f5067ec46d0afcfd` |
| read-heavy 材料レポート | `output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/reports/backoff-sweep-read-heavy_report.md` | `8c9454316cc4aac607022a007a72187f1e20846c1c5a7c66c753885aa4d58379` |
| 較正 (records) | `output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json` | `751304772367418806eb6e63c9715cd430315066420e9e3e4c91bf356195eef5` |
| 較正 (between-run rr5) | `output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json` | `200ab13614344769bbceaa4f7efe8c4411c4f6d764b3a5c036b77036498b9a11` |
| 較正 (between-run rr50) | `output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr50_rmw0.json` | `4040eda140572ea0f79d1b16854fc1db84ed18b2de13d7eacdde25ce45971dc8` |
| 較正 (between-run rr95) | `output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json` | `a6d1657885b2c855a797b71b8565e6c21d282bfb62c94395884b4ba1eac555c5` |
| profile JSON (+38.5% の出所。headline ではない) | `output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.json` | `e99932213a571561c87f5ac253e19f59a81382718bb0cf08a9c64ea64281d184` |
| profile md | `output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.md` | `7d419391f9e9f8e205d87b5ca5b0b16eb57b5ebc73ce904adf47c8ee64e9e8c8` |

### 5.2 図と導出索引 (本稿の数値の出所ではない。§2.3 の `facts` の転記元は provenance JSON)

| artifact | path | SHA-256 |
|---|---|---|
| fig2b provenance | `docs/paper-story/figures/fig2b_backoff_sweep_3workload.provenance.json` | `2cdcf9234df0394ff4df389fe5dbebf0f3c9d834e93d36831a152d9ee6b88ffe` |
| fig2b PNG | `docs/paper-story/figures/fig2b_backoff_sweep_3workload.png` | `d72054607bef4d1694d3c3f68e213c9fffcad08e49460709e8df47b247738b54` |
| fig2b PDF | `docs/paper-story/figures/fig2b_backoff_sweep_3workload.pdf` | `353d403dc8746b432d04f28ac9b0dafc6da53fc367d7ff8074e3a3a0ed64e735` |
| A-3 一本化 insight (導出索引、`authority: none`) | `output/insights/2026-08-25_paper-story-a3-gain-unification/README.md` | `7f280b9f57c41850f5ae41f99600ec4f09e4fb7d4104669f4c3b51f3f3c8b31d` |
| A-3 の前稿 (write-heavy / balanced のみ) | `output/insights/2026-08-24_paper-story-a3-evidence-integration/README.md` | `12e93572a2aa4f5943f4923d13ba43c89b59a956740a0edba9039bbc71961ac9` |
| 層 3 dossier (3.2 節が同じ 3 値を無 backoff label で持つ) | `output/reports/layer3_paper_evidence_dossier.md` | `860697175d85cd645945465bccc66119f04d4e8297f8a54e310232151ee440a9` |

fig2b の PNG / PDF の SHA-256 は provenance JSON の `outputs[]` の記載と一致する。図の再現手順・キャプション正文・proof chain は
`figures/README.md` の fig2b 節が正本である。

### 5.3 裁定

- D18 — 合成 variant を inert patch (`patches/`) に置く (静的 backoff の `BACKOFF_FIXED`)。
- D19 — noise floor の 2 種分離、採否 floor は between-run の保守値 3.0%。
- D20 — 診断計器 `BACKOFF_NOINLINE` は inert patch、perf 下 tps は headline 非使用 (§3 限定 5・6)。
- D496 — 性能比較は同一 campaign 内の対測定で行う (§3 限定 1 の根拠)。
- D497 — 計測器の有無は性能主張の権威に影響しない (§3 限定 6)。
- D1100 / D1525 — 論文採用の性能値は別 boot で取り直す、Pegasus は充足にならない (§3 限定 2)。
- D1506 — 既定 adaptive を単独基準線に使わない (§3 限定 7)。
- D1631 — results 系列の設置と規則。
- D1993 — 項 4 (certification は旧 3 値へ遡らない)、項 6 (3 走行をプールしない、符号一致は記述的照合) (§3 限定 3・4)。
- D2120 項 15 — 単独 results 稿は権威 bytes から作る既存経路であり、層 3 の材料レポートと同一視しない。
- 論文ストーリー 2026-09-20 版 §8「この版が採る P2-4 の exact claim」の (性能) と但し書き 1・3 の文言 (本稿の限定 1・2 の
  言い方を揃える出所。数値の出所ではない)。

### 5.4 値の出所 (転記した数値ごと)

| 数値 | 出所 |
|---|---|
| 論文値 +38.3% / +11.3% / −6.6% と未丸め値 | §2.1 の式を WAL の `median_tps` に適用 (本稿の再計算)。A-3 insight の再計算表 (38.328803879% / 11.268232226% / −6.642987663%) と一致 |
| median tps・5 反復・cv・abort 率 (24 genome) | 各 WAL の `bench_done.payload.median_tps` / `tps` / `cv` / `leading_indicators.abort_rate` |
| IPC (静的 6 点 × 3) | 各 `.dat` の `ipc` 列。WAL `leading_indicators.ipc` を小数 3 桁に丸めた値と一致することを本稿が確認 |
| IPC (無 backoff・adaptive × 3) | 各 WAL `leading_indicators.ipc` を小数 3 桁に丸めた |
| genome 文字列・variant ID | 各 WAL の `build_start.payload.genome` と `variant` |
| configure / build command、binary hash、cache 状態 | 各 WAL の `build_done.payload` (`perf_configure_cmd` / `perf_build_cmd` / `trace_bin` / `perf_bin` / `trace_cached` / `perf_cached`) |
| `run_cmd` | 各 WAL の `bench_done.payload.run_cmd` |
| `verify_done` の 4 field | 各 WAL の `verify_done.payload` |
| `search_config`・`ccbench_commit`・`spec_content` | 各 `campaign.lock` |
| 完全な CCBench commit と日時 | pin 済み CCBench repository の履歴 (`git log` で短縮 token を解決)。A-3 insight の条件表と一致 |
| 時刻 (JST) | 各 WAL の `ts` (epoch 秒) を `TZ=Asia/Tokyo` で換算 |
| 標本平均の `facts` / `baselines` / `generated_utc` / epoch | fig2b provenance JSON |
| 平均比 +38.1 / +11.4 / −6.9% と未丸め値 | provenance の `best_M` / `none_M` に §2.1 の式を適用 (本稿の再計算)。`figures/README.md` キャプション正文の記載と一致 |
| 較正記録の値 | §1.6 の各 JSON |
| profile の値 1,867,747 / 2,586,112 と +38.5% の未丸め値 | profile JSON の `rows[].tps_median` (`backoff_us` 0 と 10) に §2.1 の式を適用 (本稿の再計算)。A-3 insight の再計算表 (38.461579646%) と一致 |
| 既定 adaptive 分母の +147.4% | write-heavy WAL の median (2,603,521 / 1,052,528) に §2.1 の式を適用 (本稿の再計算)。A-3 insight の記載と一致 |
| +39.0 / +12.9 / −7.1%、+42.2 / +11.7% | A-3 insight の参考表の記載。本稿は再計算していない (§4.3) |
| 材料レポートの「判定」行 | 各 `_report.md` の逐語 |

### 5.5 同じ結果についての既存の記述 (本稿の出所ではない)

- `docs/paper-story/2026-09-20.md` §8「この版が採る P2-4 の exact claim」(性能) と「A 群に入れない、決着済みの項目」の A-3、§4 の
  図 2b、§7 の恒久項目。
- `docs/paper-story/claim-evidence/2026-09-20.md` の C1 (性能) / C2 (正しさ) / L02 / L03。
- `docs/paper-story/figures/README.md` の fig2b 節 (キャプション正文、旧図 `fig2_backoff_mechanism.png` の誤記、2026-08-26 の
  分類語の訂正、再現手順)。
- `output/insights/2026-06-22_p2-case-study-backoff-synthesis.md` (P2-4 の当時の記録。A-3 insight は「insight の表題日を
  read-heavy の測定日として使わない」と注意する)。
- 凍結スナップショット `docs/paper-story/2026-07-10.md` / `2026-08-23.md` (旧図 `fig2_backoff_mechanism.png` のキャプションに
  baseline の誤記を含む。凍結物なので訂正されない)。
