# [T-1998] balanced stock-inline 対の結果節 — 事前登録 v1 の下で `accepted` (測定 2026-09-13、認証 2026-09-14)

**これは投稿本文ではない。** 論文の結果節・表へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む。
D2120 項 15 が「paper-story の単独 results 稿は権威 bytes から作る既存経路であり、層 3 の proof chain 付き
材料レポートと同一視しない」と定める)。英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の既存の稿を改めるものではない。** 2026-09-16 の横断稿 (`2026-09-16-b7-three-run-materials.md`) は
同じ走行を A-2 / A-6 と併記した B-7 の材料として有効なまま残る。**本稿は横断稿から 1 行も引き継がず、
一次資料全体 (事前登録 v1 の blob、成果物 root の権威 bytes、campaign lock と WAL、投入受領証、consumer の
判定 JSON、4 つの insight README、裁定) から作り直した。** 横断稿の値と一致するかどうかは本稿の検算に使っていない。

**`accepted` は consumer (事前登録 v1 に束縛された解析器) の出力であって、研究の成功宣告ではない。**
protocol は「baseline (無 backoff) と target (静的 fixed 5 µs) の各 5 標本の median の比」を問い、
それを受理条件の全部を通した上で返した、という事実である。有意差の判定ではなく、区間推定も持たない。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

**1 protocol (事前登録 `docs/t1998-balanced-stock-inline-preregistration.md` v1) の 1 試行**である。
試行は 2026-09-13 に投入された job 1 本 (Pegasus `995755.nqsv`、group `t1998-balanced-stock-inline-20260913T132723Z-548740`、
workload `balanced` のみ) で、producer (`backoff-sweep`) が 8 genome を測り、consumer
(`orchestrator/campaign/t1998_stock_inline_pair.py` の `consume_balanced_stock_inline_pair`) が
事前登録の 2 点だけを読んで判定した。**投入は 1 回だけであり、2 本目の試行は存在しない**
(事前登録 §7 の「投入は 1 回だけ」による。2026-09-15 の wave も再投入していない)。

### 0.2 書くもの

- 事前登録 v1 が**結果を見る前に**固定した 2 点と identity、および判定の規則。
- 成果物が記録した identity が事前登録と一致したこと (項目ごと)。
- consumer の判定 (`accepted`、ratio、improvement_percent) と、事前登録 §8 が「報告に必ず含めるもの」と
  定めた全項目。
- 登録 2 arm の 5 標本・median・変動係数・`unstable`、producer の付随記録 (abort 率・latency・実行 argv)。
- 正しさの記録 (campaign WAL の `verify_done`) と、その強さの限定。
- producer が測った 8 点の記録 (**推定量には入れない**。§2.4)。
- 投入から認証・再解析までの時系列。
- 限定 (§3) と、権威 bytes・WAL・事前登録・裁定の対応が確かめられない箇所 (§4「欠落」)。

### 0.3 書かないもの

- 事前登録前 (2026-09-07) に A-5 経路で取れた balanced の生値。事前登録 §3 がその存在を開示し
  D1874 が「本項の主張へ転用しない。文脈としてだけ残す」と定めた。**本稿は数値を書かず、推定量にも入れない。**
- 8 点のうち登録 2 点以外の値から導く命題 (最良点・最適量・機序)。事前登録 §2 / §6 が禁じる。
- A-2 / A-6 との集計・プール・横断の結論 (D1993 項 6)。B-7 の要件充足 (D2044 項 3)。
  A-1 の完了・A-5 の充足 (§3)。
- 旧 headline (+11.3 %) の「再現」。事前登録 §3 は旧値を期待値として固定していない。
- write-heavy / read-heavy についての主張。事前登録 §9 が対象外と定める。
- 研究としての成功・失敗・新規性の宣告 (D12)。

---

## 1. 条件 — 結果を見る前に固定したもの

### 1.1 事前登録 v1 が固定した 2 点

事前登録 v1 (blob sha256 `464e3af59a1ef0f776cad022a52ab87e1fdf2709abfc2062c058203bc813719c`、
成果物側・解析規則側の 2 定数とも同値、Erratum 節なし) は §2 で次の 2 点だけを比較対象とする。

| arm | 意味 | genome (canonical) |
|---|---|---|
| baseline | backoff を使わない対照 | `silo\|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| target | 静的 fixed 5 µs | `silo\|BACKOFF_FIXED=5,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |

workload は balanced (`ycsb_zipf_skew=0.9`、`ycsb_rratio=50`、`ycsb_rmw=0`)。事前登録 §2 は
「**producer は 8 点を測る。本書が読むのはそのうちの 2 点だけである。**残り 6 点を推定量へ代入しない。
測定後に最良点を選ぶ (argmax) ことをしない」と書く。同 §2 は、この 2 点が 2026-08-28 の precheck で
既存 genome と既定値から確定したもので、2026-09-07 の生値から選んだものではないと明記する。

事前登録 §6 の判定規則 (consumer の定数と計算が固定するものの書き写し):
各 arm の sample 数は 5、要約量は 5 sample の median、`ratio = target の median / baseline の median`、
`improvement_percent = (ratio − 1) × 100`、どちらか一方でも `unstable` なら対全体を `inconclusive` とし
`ratio` と `improvement_percent` を `null` にする、事後に最良点を選ばない。
consumer の module 定数もこれと一致する (`EXPECTED_SAMPLE_COUNT = 5`、`EXPECTED_PRODUCER_POINT_COUNT = 8`、
`TARGET_FIXED_US = 5`、`WORKLOAD = "balanced"`。現行木の `t1998_stock_inline_pair.py` で確認)。

### 1.2 事前登録 v1 が固定した identity

事前登録 §4 / §5 (機械可読 block) の値。**測定を 1 度も走らせる前に固定された** (§4 冒頭の逐語)。

| 対象 | 事前登録の値 |
|---|---|
| CCBench gitlink (hex40) | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| 環境契約 digest (`pegasus`) | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` |
| job body script (`tools/pegasus/a5_second_boot_backoff_sweep.sh`) の sha256 | `dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8` |
| baseline の source bytes sha256 | `2d691b45afd02a7979b1872eeb0a5c5c58223550892331b31641599aa239a2c6` |
| target の source bytes sha256 (patch 適用下) | `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12` |

`repository_commit` は block に無く、§4.3 の規則 (成果物が記録する `repository_commit` における事前登録 blob の
sha256 が成果物側定数と一致すること) で決まる。事前登録 §4.2 は、patch を当てずに計算した target の値
`6454d9f34b04fdb148bc3324c5b07786d933dcc1ab0f7267aa0b91d414f70a84` を「正しくない。本書はこれを受理しない」と
明記している (この値は §2.4 の表で別の genome の記録として現れる)。

### 1.3 producer の測定条件 (成果物と、lock が束縛する code から)

campaign WAL の `bench_done.run_cmd` は両 arm とも実行ファイルの後に
`-thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=2100 -ycsb_zipf_skew=0.9 -ycsb_rratio=50 -ycsb_rmw=0`
を持つ (launch prefix なし。`pegasus` 契約の `numactl=()` に対応する)。実行ファイルは configure が指定した
build directory (`-DCCBENCH_TRACE=0`、`-DCMAKE_BUILD_TYPE=Release`、`-DENABLE_SANITIZER=OFF`) の
`cc/silo/ycsb_silo.exe` である (trace-disabled の性能 build)。

campaign.lock の `identity_preimage` は `search_config` として `records 1000000`、`threads 48`、
`sweep_us [2, 5, 10, 25, 50, 100]`、`workload balanced`、`ycsb {rmw 0, rratio 50, zipf_skew 0.9}`、
`measurement_env pegasus`、`base L-W0` を持つ。標本数 5 と実行時間 3 秒は lock が束縛する
`orchestrator/campaign/p2_2.py` (blob `9b30a7ad764f7a2dac0554349af9a46f08587db7e9ecdc91bc8501f8d2734db3`、
`repository_commit` の現物と一致) の `RECORDS = 1_000_000` / `THREADS = 48` / `EXTIME = 3` / `REPS = 5` から来る。
`ycsb_max_ope` は argv に現れない。

8 genome の集合は `orchestrator/campaign/backoff_sweep.py` の `genomes()` (無 backoff、CCBench 既定 3 定数の
adaptive、静的 2 / 5 / 10 / 25 / 50 / 100 µs) で、**この file は lock の `contract_loader_blob_sha256s`
(63 blob) に含まれない**。束縛は `repository_commit` 経由に限られる (§4)。

### 1.4 成果物が記録した identity — 事前登録と全項一致

| 対象 | 成果物の記録 | 出所 | 事前登録との照合 |
|---|---|---|---|
| repository_commit | `a551cdd3014708993475108f014aacbf32c21137` | `result.json`、`reservation.json.source_binding`、`campaign.lock.authority.contract_loader_commit`、submit receipt の 4 者 | この commit の事前登録 blob の sha256 = `464e3af5…` (本稿で `git show` から再計算し一致) |
| CCBench gitlink | `511c9538e4e8efa54b45cda62e72389ed3b706ec` | `result.json.ccbench_commit`、`reservation.json.source_binding` | 一致。`a551cdd3` の gitlink も同値 (再計算)。lock と WAL は 7 桁 `511c953` |
| 環境契約 digest | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` | `campaign.lock.authority.environment_contract_sha256`、WAL の各 `commit.contract_sha256` | 一致 |
| job body script sha256 | `dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8` | `reservation.json.binding.script_sha256`、submit receipt の `job_script_sha256` | 一致。`a551cdd3` の同 file の blob からも再計算し一致 |
| baseline の source bytes sha256 | `2d691b45…a2c6` | WAL `build_start.build_admission.source` (`src_token` = `stock`) | 一致 |
| target の source bytes sha256 | `678b7203…0b12` | 同上 (`src_token` = 同じ sha256) | 一致 |

WAL 40 record の `env_tag` はすべて `pegasus`。両 arm の `build_admission.source` は
`tracked_clean = false`、`tracked_paths = ["cmake/Options.cmake", "include/backoff.hh"]`、
`tracked_diff_sha256 = 29aef2bc1b9f30524ad8ceeff59ffdbfda626612986cb7851cce8accbdaa3682` で、
**patch `patches/silo-backoff-fixed.patch` が当たった木で両 arm とも build されたことを記録している**
(baseline は patch の inert 枝で `src_token` が `stock` のまま、target は合成 token)。

その他の identity: `campaign_id` = `backoff-sweep-silo-balanced-sweep-0dd37c05`、
lock sha256 `ba24c65d01ce80bb17d0ae1ff8f5242078c2cb7b9a6b3c502959542b61ba0c61`、
WAL sha256 `154ab894a9955885036fcaff03478001153ba015c50f395cbb59b3e20dcf594e`
(いずれも `result.json` の `lock_sha256` / `wal_sha256` と、本稿の再計算が一致)。
node `bnode024`、`boot_id` `a58d5461-525d-48b5-a442-e13f18b5d5d8`、`boot_epoch` 1788999892、
queue `gen_S@nqsv`、`Remaining Elapse` 7200 秒の予約。toolchain は `x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`、
`cmake version 3.22.1` (`result.json.toolchain` と WAL `build_done.toolchain` の 3 key 射影)。

---

## 2. 結果

### 2.1 consumer の判定 — 事前登録 §8 が報告に求める全項目

| 項目 | 値 |
|---|---|
| status | **`accepted`** |
| reason | `preregistered-balanced-stock-inline-pair` |
| ratio | 1.1122537536191646 |
| improvement_percent | **11.225375361916456** |
| 拒否 code / field / 期待値 / 実際の値 / arm | 該当なし (拒否ではない) |
| `unstable` | baseline false、target false (両 arm とも `bench_done` と `commit` の値が一致) |
| 事前登録の版 | v1 |
| 成果物側の sha (`MEASUREMENT_TIME_PREREGISTRATION_SHA256`) | `464e3af59a1ef0f776cad022a52ab87e1fdf2709abfc2062c058203bc813719c` |
| 解析規則側の sha (`CURRENT_PREREGISTRATION_SHA256`) | 同値 |
| 事前登録前の値 (§3) | 混ぜていない (本稿にも書いていない) |

出所は consumer の判定 JSON (`decision-final.json`、2026-09-14 03:41 JST、sha256
`73ac9c34afb0819c1389d183075d298e21ce9467467ccc8bbe2ed4968f68d0f6`)。同 JSON の `outcome` は `accepted`、
`prereg_commit` は `a551cdd3…`、`preregistered` block は事前登録 §5 と同値である。
`ratio` と `improvement_percent` は producer の `result.json` (`ratio`、`improvement_percent`) とも全桁一致し、
本稿が 5 標本から再計算した値 (median 比 4330570 / 3893509) とも全桁一致する。

**認証は再測定をしていない。** 2026-09-13 の 1 回目の解析は consumer が `performance-build-not-trace-disabled`
(field `wal.bench_done.run_cmd.executable`、arm baseline) で拒否した。原因は測定側ではなく consumer 側の
2 系統の述語 (`linux-baremetal` 契約の `numactl` prefix を literal で要求、回収成果物から再導出できない
toolchain digest の腕内等式) で、2026-09-14 に是正 (commit `4d7cd40a9b125fd5bc04e2d47a980d8b772c9a31`) した後、
**同じ保全成果物**を通して `accepted` を得た。是正で事前登録の bytes と 2 つの sha 定数は動いていない。
**是正のうち toolchain digest の腕内再導出の撤去は受理集合を広げる変更である** (2026-09-14 README §2.2 の逐語
「受理集合は広がる」)。残る検査は腕間の digest 一致・manifest 一致・`result.toolchain` との一致で、
「両腕の digest を同じ別値へ置換した改竄は、この層では拒否できない」が明記された非保証範囲である。

2026-09-15 に、着地後の main (`0600887d92538b3f34d894f9674d202d0a29a578`) の consumer から同じ保全成果物を
通し直し、status / reason / ratio / improvement_percent / 両 arm の 5 標本・median・変動係数・identity が
2026-09-14 の記録と全桁一致することが記録されている (同日の insight README。その判定 JSON は保全されていない。§4)。

### 2.2 登録 2 arm の生標本

| arm | variant | 5 標本 (tps、`bench_done.tps` の記載順) | median | 変動係数 (`cv`) | `unstable` | `high_variance` |
|---|---|---|---:|---:|---|---|
| baseline | `84319b1127a6` | 4079966 / 3891020 / 3978513 / 3859794 / 3893509 | 3,893,509 | 0.022721229214372803 | false | false |
| target | `93c62227a2d3` | 4437166 / 4326276 / 4361949 / 4330570 / 4289164 | 4,330,570 | 0.012790608817328908 | false | false |

- median は本稿が 5 標本から再計算して `bench_done.median_tps`、`commit.fitness_tps`、
  `result.json` の `no_backoff_median_tps` / `target_median_tps`、consumer JSON の `median_tps` と一致した。
- `cv` は producer の field で、値は**標本標準偏差 (分母 n−1) ÷ 標本平均**と倍精度で全桁一致した (本稿の再計算)。
  表示用に丸めるなら baseline 2.27 %、target 1.28 % (producer の stdout が印字した丸め)。
- `rounds` は両 arm とも 1、`cv_history` は 1 要素。`settled` は baseline `true`、target `null`
  (producer の field。consumer は読まない)。`bench_wall_s` は baseline 16.738 秒、target 16.687 秒。
- 付随記録 `leading_indicators`: baseline `abort_rate` 0.6795 / `latency_ns` 12328.2109、
  target `abort_rate` 0.4613 / `latency_ns` 11083.9913。`llc_miss_rate` と `ipc` は `null`
  (`perf_preflight` が `unavailable`、`perf_counter_statuses` = `not_required`、`claim_scope.throughput` = `eligible`)。
  `abort_rate` の定義は成果物に無い (§4)。
- 性能 binary の sha256: baseline `660543647aa9b8bf0b6ff087ec461c901fd186296dc2751cd7d1deb89ae565d9`、
  target `6c89ebd91efddfd6c01fa5fbff1d5d6cf16e8488b7e2fc85f98ec76e1a8dfec4` (WAL `build_done.perf_bin_sha256`、
  consumer JSON の `performance_binary_sha256` と一致)。

### 2.3 正しさの記録 — campaign WAL の `verify_done`

| arm | verdict | certified | anomalies | commits | aborts | `workload.tag` | proof_surfaces (X / P / I) | trace binary sha256 |
|---|---|---|---:|---:|---:|---|---|---|
| baseline | `serializable` | true | 0 | 642639 | 252104 | `legacy` | evidence-present / evidence-present / evidence-absent | `651887e745c32a15672aa79cbd88d2fa62092a60a8c83f89f2e71a1021324e80` |
| target | `serializable` | true | 0 | 582099 | 165681 | `legacy` | evidence-present / evidence-present / evidence-absent | `1d71de8da2f18ef2094158a39d3890fdf1bd952d6ffba806f5778b872ef9e84b` |

- `verify_done` は各 arm 1 record (`commit.verify_configs = ["legacy"]`)、`commit_verification_receipt.verifier_evidence`
  も 1 件ずつ (`verifier_result_sha256` baseline `613f180e…`、target `d94b3909…`)。
  `commit_receipt_id` は baseline `c0465f86d63c17f2a701b9581c526716b611aba7a4267450ceaf4ddbad414fe2`、
  target `55246bf5739080fb73be059f61d2d715ecdbdc08aff0699c40d1a00c68986bf6`。
- 検査は trace-enabled の別 binary (`trace_bin`) で、性能 binary とは別走である (絶対規律 1)。
  WAL の時刻は両 arm とも `build_done` → `verify_done` → `bench_done` → `commit` の順。
- **検査条件の argv は成果物 (WAL・`result.json`・job stdout) のどこにも記録されていない。**
  lock が束縛する `orchestrator/campaign/pipeline.py` (blob `2423849c893f7b69cfab1e11f9d6433e1f0812b77dcc0399b5db5f706393ecdd`、
  `repository_commit` の現物と一致) の `CorrectnessWorkload` 既定値は `ycsb_tuple_num 200`、`ycsb_zipf_skew 0.9`、
  `ycsb_rratio 50`、`ycsb_rmw true`、`ycsb_max_ope 5`、`thread_num 4`、`extime 1`、`reps 1` である。
  **これは束縛された code から導いた値であって、成果物の記録ではない。** 性能を測った 48 thread・1,000,000 records・
  `rmw 0`・3 秒の条件そのものの検査ではない。
- **したがって、この走行の正しさの記録は「登録 2 arm とも legacy 条件で 1 回ずつ serializable / certified /
  anomaly 0」までである。** A-2 / A-6 の attempt が持つ legacy 1 回 + 性能条件側 5 回の形式ではなく、同じ強さではない
  (本稿はその比較を書かない。強さの違いは形式の違いとして書く)。
- `result.json` に `correctness` 欄は無い (`a5-second-boot-result/v1` の 24 key に含まれない)。
  正しさの記録は WAL だけが持つ。

### 2.4 producer が測った 8 点の記録 — 推定量には入れない

producer は 8 genome を WAL の記載順に測り、8 点とも `commit` (abort record 0、`.failure.json` なし)。
**事前登録が読むのは行 1 と行 4 の 2 点だけである。他の 6 点の値から本稿は何も導かない**
(最良点・最適量・地形・機序を書かない。事前登録 §2 / §6)。producer の stdout は 8 点を throughput 順に並べた
「ランキング」を印字するが、事前登録も consumer もそれを読まない。

| # | variant | `BACK_OFF` | `BACKOFF_FIXED` | `src_token` | 5 標本 (tps) | median | `cv` | `unstable` | verify | commits / aborts (verify) |
|---:|---|---:|---:|---|---|---:|---:|---|---|---:|
| 1 | `84319b1127a6` | 0 | −1 | `stock` | 4079966 / 3891020 / 3978513 / 3859794 / 3893509 | 3,893,509 | 0.0227 | false | serializable / certified / 0 | 642639 / 252104 |
| 2 | `602b4ce9c788` | 1 | −1 | `stock` | 1273149 / 1265586 / 1292091 / 1180562 / 1228453 | 1,265,586 | 0.0354 | false | 同 | 282460 / 8925 |
| 3 | `82ea3a7b8618` | 1 | 2 | `d786db57…` | 4656913 / 4350513 / 4451117 / 4348124 / 4442208 | 4,442,208 | 0.0282 | false | 同 | 628579 / 225147 |
| 4 | `93c62227a2d3` | 1 | 5 | `678b7203…` | 4437166 / 4326276 / 4361949 / 4330570 / 4289164 | 4,330,570 | 0.0128 | false | 同 | 582099 / 165681 |
| 5 | `a7f8486e1116` | 1 | 10 | `16c29935…` | 3934337 / 3910016 / 3887133 / 3903443 / 3911884 | 3,910,016 | 0.0044 | false | 同 | 529897 / 122126 |
| 6 | `f35115998eb9` | 1 | 25 | `8299956a…` | 3067278 / 3083495 / 3057439 / 3066391 / 3059296 | 3,066,391 | 0.0034 | false | 同 | 442829 / 71493 |
| 7 | `56df98d73105` | 1 | 50 | `96608c1e…` | 2433591 / 2424838 / 2419177 / 2435450 / 2431951 | 2,431,951 | 0.0028 | false | 同 | 388097 / 43699 |
| 8 | `ada51d144af8` | 1 | 100 | `9fea0c83…` | 1871719 / 1862051 / 1876195 / 1870346 / 1860962 | 1,870,346 | 0.0035 | false | 同 | 336623 / 24815 |

- 表の `cv` は 4 桁に丸めた表示。全桁は WAL にある。8 点とも `high_variance` false、`rounds` 1、
  `proof_surfaces` は X / P `evidence-present`、I `evidence-absent`。
- 行 2 (`BACK_OFF=1, BACKOFF_FIXED=-1`、CCBench 内蔵の adaptive backoff) の `source_bytes_sha256` は
  `6454d9f34b04fdb148bc3324c5b07786d933dcc1ab0f7267aa0b91d414f70a84` で、事前登録 §4.2 が「patch を当てずに
  計算した target の値。正しくない」と退けた値と同じ bytes である。**これは記録の一致であって、本稿が
  何かを導く根拠ではない。**
- **行 3 (2 µs) の median が行 4 (5 µs) より高いことを、本稿は結論にしない。** 事前登録は結果を見る前に 5 µs を
  固定し、事後の最良点選択を禁じている。

### 2.5 時系列 (一次資料の時刻。UTC は receipt / WAL の epoch、JST は qstat / job 末尾の表記)

| 時刻 | 事象 | 出所 |
|---|---|---|
| 2026-09-11 09:59:01 JST | `repository_commit` `a551cdd3…` (事前登録 v1 を含む fold commit) | `git log` |
| 2026-09-13 13:27:23Z (22:27:23 JST) | 投入 (`submit_t1998_balanced_stock_inline.sh`、1 回)。receipt `manifest` / `submitted` | submit receipt、qstat `Created Request Time` |
| 13:27:36Z | job `995755.nqsv` 開始、node `bnode024` | qstat `Started Request Time`、`reservation.json` |
| 13:28:33.980Z 〜 13:29:57.002Z | baseline: `build_start` → `build_done` (13:29:23) → `verify_done` (13:29:40) → `bench_done` (13:29:56) → `commit` | WAL `ts` |
| 13:32:41.395Z 〜 13:34:02.916Z | target: `build_start` → `build_done` (13:33:31) → `verify_done` (13:33:46) → `bench_done` (13:34:02) → `commit` | WAL `ts` |
| 13:39:22.837Z | 8 点目の `commit` | WAL `ts` |
| 13:39:23Z (22:39:23 JST) | job 終了、Elapse 712 秒 | job stdout 末尾 |
| 2026-09-13 (同日) | 1 回目の解析: consumer 拒否 `performance-build-not-trace-disabled` | 2026-09-13 insight README §2 |
| 2026-09-14 03:41 JST | consumer 是正後の判定 `accepted` (`decision-final.json`) | 同 file の mtime、2026-09-14 insight README §1 |
| 2026-09-14 03:43:27 JST | consumer 是正の commit `4d7cd40a9…` (main への取り込みは同日 11:40:29 JST の `291892b90…` 以前。§4 (j)) | `git log`、2026-09-14 insight README §4、2026-09-15 README §1 |
| 2026-09-15 (main `0600887d9…` は 14:24:28 JST の commit) | 着地後の main で再解析、全桁一致 | 2026-09-15 insight README §2、`git log` |

### 2.6 producer の `complete` と consumer の `accepted` は別の出力

`result.json.status` = `complete` は producer (A-5 job body の finalizer) の出力で、8 点の commit と
`result.json` の生成までを言う。`accepted` は consumer の出力で、事前登録 §4 / §5 との identity 照合、
2 点の genome 一致、標本数、median の再計算一致、`unstable`、admission と全 `commit` の verifier receipt の検査を
通した上での判定である。**前者は後者を含意しない** (2026-09-13 は前者が `complete` で後者が拒否だった)。

---

## 3. 限定 — この結果が言わないこと

1. **各 arm 5 標本の median 比であって、A-1 の対差平均ではない。** A-1 (policy
   `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`) の推定対象は「均衡 5-rep 配置下の対差の算術平均」
   (`pairing.estimand`、contrast `variant-minus-baseline`、`arm_block_reps 5`、`group_pairs 10`) で、
   balanced の腕対応は同じ対 (fixed 5 µs 対 no-backoff) だが、配置・推定量・区間推定の有無が違う。
   **T-1998 の `accepted` を A-1 の完了と読まない。**
2. **A-2 / A-6 とプールしない (D1993 項 6)。** protocol も事前登録も attempt も別である。
   3 走行を 1 つの横断実験として集計せず、符号の一致を書くとしても記述的照合に留め、再現判定にしない。
3. **B-7 の要件充足ではない (D2044 項 3)。** B-7 (全 workload の退行込み報告) は「同一 variant の横断比較と
   床値超の判定」を求め、本稿はそのどちらも供給しない。記述的な報告としての利用は許され、要件充足へは昇格しない。
4. **有意差の判定ではなく、信頼区間も無い。** 事前登録 §6 の判定式は median 比だけを定義し、
   consumer は `accepted` / `inconclusive` の 2 値と拒否しか返さない。「11.2 % 速い」は点推定である。
5. **1 job・1 boot・1 node (`bnode024`) の測定である。** 走行間ばらつき・cold boot・温度ドリフトを含まない。
   A-5 (別の起動での取り直し) は D1525 により Pegasus では充足せず、事前登録 §9 も A-5 を解除しない。
6. **旧 headline の +11.3 % の予測的再現ではない。** 事前登録 §3 は旧値を期待値として固定していない。
   近い値が出たことは事後の観察である。旧値 (旧 `linux-baremetal` 環境) と本値をプールしない。
7. **正しさの記録は legacy 条件 1 回ずつである** (§2.3)。性能条件そのものでの検査ではなく、検査条件の argv は
   成果物に無い。A-2 / A-6 の形式 (legacy 1 回 + 性能条件側 5 回) とは同じでない。
   `certified` は正しさゲートの判定であって、性能の判定ではない。
8. **8 点のうち 6 点から何も導かない** (§2.4)。最適 backoff 量・地形・機序・「2 µs の方が速い」は本稿の命題ではない。
9. **事前登録前の生値 (2026-09-07) を混ぜていない** (D1874)。本稿は数値を書いていない。
10. **write-heavy と read-heavy は対象外** (事前登録 §9)。本走行は balanced の 1 job だけである。
11. **compiler の同一性は証明していない。** 事前登録 §4.2 の source digest はログインノードの `g++` で導かれ、
    計算ノードの `g++` が同じ前処理結果を与えたことは、この走行が `source-identity-unbound` に落ちなかったという
    **1 回の観測**である (2026-09-15 の再解析は同じ成果物の再読なので独立な観測ではない)。
12. **toolchain digest の腕内対応は検証していない** (§2.1)。consumer が検査するのは腕間の一致までで、
    「両腕の digest を同じ別値へ置換した改竄」はこの層で拒否できない。
13. **投入器の同一性は成果物から復元できない。** 成果物が束縛するのは job body (`dff913cb…`) までで、
    投入器の sha256 `dff1f9d0662a519e8427f6aa7571998ea8ba08f70d98931e960aec4f7813add8` は投入器自身が書いた
    receipt にだけある (consumer JSON の `submitter_identity_recoverable = false`、`launcher_binding_scope =
    job-body-script-sha256-only`)。
14. **診断 build の排除は arm 別 source digest の一致に依る。** 事前登録 §9 のとおり、genome と configure の
    明示値検査だけでは排除できない (consumer JSON の `explicit_diagnostic_marker_check_is_sufficient = false`)。
15. **`accepted` は consumer の是正後に出た。** 是正 (2026-09-14) は受理集合を広げる変更を 1 件含む (§2.1)。
    事前登録 §6 の判定規則は動いていないが、「事前登録された受理条件は 1 つも動かない」だけを根拠にしない。
16. **他の成果物での欠陥不存在は言えない。** 言えるのは「この成果物では追加の拒否に遭遇しなかった」までである
    (2026-09-13 README §7 の追補、2026-09-14 README §5)。
17. **`ratio` / `improvement_percent` は producer の `result.json` にも書かれている**が、本稿が採るのは consumer の
    出力である。両者が一致したことは検算であって、producer の値を認証したのではない。
18. **本稿は図を持たない。** `docs/paper-story/figures/` に T-1998 の凍結図は無い。表の値はすべて権威 bytes からの転記である。
19. **`abort_rate` / `latency_ns` は比較の根拠にしない。** producer の付随記録で、定義は成果物に無く (§4)、
    事前登録の判定規則に含まれない。
20. **本稿の「一致」は本稿の再計算と現物の照合であり、独立監査ではない。** 再計算は 1 主体 (本稿の執筆者) が
    行った。

---

## 4. 欠落 — 権威 bytes・WAL・事前登録・裁定の対応が確かめられない箇所

- **(a) patch file と `tracked_diff_sha256` の対応。** `repository_commit` の `patches/silo-backoff-fixed.patch` の
  sha256 は `a5e0710c3f76744755b58ec66024c277daba00e49ce3cbf3d6d263cd7228580a`、WAL の `tracked_diff_sha256` は
  `29aef2bc…` で、後者の pre-image は `git diff --binary HEAD` の出力 (`source_digest.py` の
  `_tracked_diff_sha256`) であり patch file そのものではない。**本稿は両者の対応を再現していない。**
  patch 適用下の source bytes が事前登録の値と一致したこと (§1.4) が、この対応の代わりに立つ束縛である。
- **(b) 2026-09-15 の再解析の判定 JSON は保全されていない。** 残るのは同日の insight README の転記だけである。
  2026-09-14 の `decision-final.json` は job dir (repo 外) にあり、本稿はその sha256 を §5.1 に書く。
- **(c) 正しさ検査の argv は成果物に無い** (§2.3)。束縛された code の既定値から導いた条件を書き分けた。
- **(d) toolchain digest の腕内再導出は不能** (§2.1、限定 12)。
- **(e) 環境契約 digest `e576e9cd…` の pre-image を本稿は再計算していない。** consumer が lock と各 `commit` の
  値を事前登録と照合したこと (判定 JSON) を採った。
- **(f) 投入器の同一性は receipt のみ** (限定 13)。
- **(g) `backoff_sweep.py` (8 点の集合と patch 適用の駆動点) は lock の loader 束縛に無い** (§1.3)。
  束縛は `repository_commit` 経由に限られ、本稿はその commit の blob (sha256
  `5d55cbbb030fd8ad33701fe23da257c7f757900d7999178b481b0c39fc0bea10`) を読んで 8 点の集合を確認した。
- **(h) `abort_rate` の定義は成果物に無い。** `repository_commit` の `orchestrator/calibrator/model.py` の注釈は
  `abort/(commit+abort)` と書くが、同 file は lock の loader 束縛に含まれない。本稿はこの値を比較に使わない。
- **(i) 認可 D1874 と test 投入の対応。** D1874 は「事前登録の実値を固定したうえで正式測定を認可する」と書き、
  実値の固定は 2026-09-10 ([T-2533]) に着地した。投入 (2026-09-13) が D1874 の認可の下で行われたことは
  2026-09-13 insight README の記述によるもので、成果物自体は認可を記録しない。
- **(j) 是正 commit `4d7cd40a9…` (2026-09-14 03:43:27 JST) の main 着地。** 2026-09-15 README は「その後 `4d7cd40a9`
  として main へ着地している」と書く。本稿が `git log --first-parent main` で確かめた範囲では、同 commit を最初に含む
  main 上の commit は `291892b909706a72d501ce711f58f5fb511c56db` (2026-09-14 11:40:29 JST) で、再解析に使われた
  main `0600887d9…` (2026-09-15 14:24:28 JST) はその子孫である。**着地の受領証 (land の receipt) は本稿では引いていない。**

---

## 5. 一次資料

### 5.1 権威 bytes (repo 外) と SHA-256 — 本稿が 2026-09-18 に再計算した値

成果物 root = `/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced`
(23 file。空 file 9 件の sha256 は `e3b0c442…` で省く)。

| file | sha256 |
|---|---|
| `result.json` (`a5-second-boot-result/v1`、1,864 bytes) | `354ecd5f6c71f26bec3adf6ba95dd3d82142d5c9deb70849180fcec19306c183` |
| `reservation.json` (`a5-second-boot-reservation/v1`、921 bytes) | `45cb2cf13f8a247d44a2275c53a7fabb60861078bcce44c99bcc15a7d13f1c7d` |
| `campaigns/backoff-sweep-silo-balanced-sweep-0dd37c05/campaign.lock` (`campaign-lock/v2`、7,951 bytes) | `ba24c65d01ce80bb17d0ae1ff8f5242078c2cb7b9a6b3c502959542b61ba0c61` |
| `campaigns/backoff-sweep-silo-balanced-sweep-0dd37c05/runs/wal.jsonl` (40 record、60,166 bytes) | `154ab894a9955885036fcaff03478001153ba015c50f395cbb59b3e20dcf594e` |
| `qstat-f.stdout` | `87f56a816d243f4f862f28b51afa1c8a6c44d0b1f2cdb3bf177acfdf64988259` |
| `env/pegasus/claims/backoff-sweep-silo-balanced-sweep-0dd37c05.claim` | `180bbcf763b1ef966d37ba012e2916f94cc76531aad308c5530827ec2a7acbfe` |
| `env/scratch-worktrees.json` | `b5d0fb86cd84f26828a2728613932d167a5deb7bb072f74791c5d2add4fca63e` |
| `env/repo-worktree-add.stdout` / `.stderr` | `2927e80c4f4fb2c812622c30f92fb233dd196405bbbd360c3c3b077cfc5e2fb4` / `bae336f46d0a8efcdc819ef186f6906b20b89b2268230e6d31cce989752299bc` |
| `env/ccbench-worktree-add.stdout` | `d905cbc70c14876a3f8117a9fb63481c63f42140cd0e29c2043eec47e7e2057c` |
| `env/dependencies/gflags-source-head.txt` / `glog-source-head.txt` | `a524a04f775caf990b5275861473507f79decf9e09d53727284db3f54292ce38` / `35ac6b5bb8c3a074e28f6e7a84873c2e50cd970d87755b9ca92f219d307c5ff8` |
| `env/worktree-remove.rc`、`qstat-f.rc` (いずれも `0\n`) | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |

同じ親 directory の file:

| file | sha256 |
|---|---|
| `t1998-balanced-stock-inline-20260913T132723Z-548740.submit.jsonl` (受領証、`manifest` / `submitted` の 2 行) | `c51521ca4b843779001f09b76b48f20cd5e8ae65d4f9566f87b14ccc93b8ba74` |
| `…-balanced.stdout` (job stdout、268 行) | `f15a82b6d3143b0300b760605ee6f5a26922c419f90b45641d8322b4b1b31b35` |
| `…-balanced.stderr` | `6788a9ae039c6f039fd80652b7f2fe6aaf4c2641804e6c546469096c91a56109` |

consumer の判定 JSON (repo 外、job dir):

| file | sha256 |
|---|---|
| `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2589-consumer-repair/decision-final.json` (2026-09-14 03:41 JST) | `73ac9c34afb0819c1389d183075d298e21ce9467467ccc8bbe2ed4968f68d0f6` |
| `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2557-balanced-stock-inline/decision.json` (2026-09-13 の拒否) | `ea613bc992c203730cb1acb044ca8d9553962b93cb68a1ae00e9e66a280f131e` |

### 5.2 repo 内 (tracked) の一次資料

- 事前登録 v1: `docs/t1998-balanced-stock-inline-preregistration.md`。blob sha256 `464e3af5…719c`
  (`repository_commit` `a551cdd3…` の blob と現行木で同値。Erratum 節なし)。
- consumer: `orchestrator/campaign/t1998_stock_inline_pair.py` (現行木。定数 §1.1、2 つの sha 定数 §2.1)。
- `repository_commit` `a551cdd3014708993475108f014aacbf32c21137` の blob (本稿が `git show` で取り出し sha256 を計算):
  `tools/pegasus/a5_second_boot_backoff_sweep.sh` `dff913cb…`、`tools/pegasus/submit_t1998_balanced_stock_inline.sh`
  `dff1f9d0…`、`orchestrator/campaign/pipeline.py` `2423849c…`、`orchestrator/campaign/p2_2.py` `9b30a7ad…`、
  `orchestrator/campaign/env_contract.py` `292bbed3…` (以上 3 つは lock の loader 束縛と一致)、
  `orchestrator/campaign/backoff_sweep.py` `5d55cbbb…` (loader 束縛外)、`patches/silo-backoff-fixed.patch` `a5e0710c…`、
  gitlink `external/ccbench` = `511c9538…`。
- A-1 の推定対象の出所: `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`
  (sha256 `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a`、`pairing.estimand`)。
- insight README (経緯・判定の記録。値の正本ではない):
  `output/insights/2026-09-08_t1998-stock-inline-parts/README.md` (最小 3 部品、到達性監査)、
  `output/insights/2026-09-10_t2533-t1998-prereg-digest/README.md` (事前登録 v1 の新設と実値)、
  `output/insights/2026-09-13_t2557-balanced-stock-inline/README.md` (投入・回収・1 回目の解析 = 拒否、§7 の追補)、
  `output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md` (consumer 是正と認証)、
  `output/insights/2026-09-15/t1998-landed-main-recheck/README.md` (着地後 main での再解析)。

### 5.3 裁定

- D1874 (2026-09-09): 事前登録の実値を固定したうえで正式測定を認可。事前登録前の生値は主張へ転用しない。
- D1993 項 6 (2026-09-14): A-2 / A-6 / balanced stock-inline 対の 3 走行を 1 つの横断実験として集計しない。
  符号の一致は記述的照合であって再現判定ではない。
- D2044 項 3 (2026-09-16): B-7 の要件充足へ昇格させない。記述的な報告の利用は可。
- D2120 項 15 (2026-09-17): paper-story の単独 results 稿 (T-2611 / T-2674 の型) を使う。層 3 の材料レポートと同一視しない。
- D12: protocol status は protocol の出力として書き、研究の成功・失敗の宣告へ拡張しない。
- 絶対規律 7: 記録された測定を現行コードとの差だけで無効にしない。本稿の値は 2026-09-13 の成果物のものである。

### 5.4 値の出所 (転記した数値ごと)

| 本稿の値 | 出所 (file / field) |
|---|---|
| 5 標本、median、`cv`、`unstable`、`high_variance`、`rounds`、`settled`、`bench_wall_s`、`leading_indicators`、`run_cmd` | WAL `bench_done.payload` (variant `84319b1127a6` / `93c62227a2d3`) |
| `fitness_tps`、`verify_configs`、`contract_sha256`、`commit_verification_receipt` | WAL `commit.payload` |
| verdict / certified / anomalies / commits / aborts / `workload.tag` / `proof_surfaces` | WAL `verify_done.payload` |
| `src_token`、`source_bytes_sha256`、`tracked_*`、`genome` | WAL `build_start.payload.build_admission.source` |
| `perf_bin_sha256`、`trace_bin_sha256`、`perf_configure_cmd`、`toolchain`、`toolchain_record_sha256` | WAL `build_done.payload` |
| status / reason / ratio / improvement_percent / identity block / 2 つの sha pin | `decision-final.json` |
| `no_backoff_median_tps`、`target_median_tps`、`ratio`、`improvement_percent`、`status = complete`、`toolchain`、`lock_sha256`、`wal_sha256`、`pbs_jobid`、`boot_*`、`perf_preflight` | `result.json` |
| `script_sha256`、`job_id`、`requested_s`、`source_binding` | `reservation.json` |
| `identity_preimage` (`search_config`)、`contract_loader_commit`、`environment_contract_sha256`、63 blob | `campaign.lock` |
| `job_script_sha256`、`submitter_sha256`、`group_id`、`submission_nonce` | submit receipt |
| Created / Started / Ended Request Time、Elapse、queue、node | `qstat-f.stdout`、job stdout 末尾 |
| 事前登録の 2 点・identity・判定規則の逐語 | `docs/t1998-balanced-stock-inline-preregistration.md` §2 / §4 / §5 / §6 / §8 / §9 |

### 5.5 同じ結果についての既存の稿 (本稿の出所ではない)

- `results/2026-09-16-b7-three-run-materials.md` — 同じ走行を A-2 / A-6 と併記した B-7 の材料。**本稿はここから
  引き継いでいない。** どちらも凍結物として残る。
- 版 `docs/paper-story/2026-09-14.md` §8 と `docs/paper-story/2026-09-17.md` §2 第 3 幕 / §7 — 同じ値を版として記述する。
  版は本稿の数値の出所ではない (README の規則)。
