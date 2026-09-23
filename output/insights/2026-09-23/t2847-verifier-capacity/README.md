# verifier の容量 — VLDB 実験が検証する trace の長さと、既存実測の外 (巡回の多い trace・参照 genome) の実測 ([T-2847] 残り (3)、2026-09-23)

- 依頼: [T-2847] の残り (3)。設計 = `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` §6 (§6.3 の手順、§6.4 の [T-2351] との関係)。
- 起点: local main `cadaf3805` (記録の前に `76d0a0c92` へ fast-forward)、CCBench pin `e9e477ca`、verifier = 同 main の `orchestrator/verifier/` (D2181 改修版以降)。
- 担当分割: (1) コーパスの test と (2) 壊し patch の変異実走は別 wave の担当で、本書は扱わない。
- 計算: Pegasus gen_S 4 job、dispatch Elapse 237 S + 328 S + 472 S + 684 S = **1,721 S (0.48 node 時間)**。投入前の見積りは 2 回に分けて出した。初回 (job A・B) = walltime の和 1.67 + 受入 1 回 0.25 = 1.92 node 時間。追加時 (段 6 の所見で足した job C・D) = A・B の実消費 565 S (0.157) + C・D の walltime の和 1.17 + 受入 0.25 = 1.57 node 時間。どちらも D2212 項 4・D2219 項 1 の確認線 (2 node 時間) を下回った (4 job の walltime をすべて足すと 2.83、受入込みで 3.08 node 時間になるが、A・B は追加の投入前に 565 S で終わっていた)。

## 1. 結論

1. **VLDB の実験が verify する経路のうち、同じ構成の実測があるのは次のものである:** 合成ループの毎回検証 (legacy、1 s・4 thread・200 レコード)、Silo の性能構成の錨 (3 s・48 thread・100 万レコード) での stock・固定 backoff・参照 genome (`p2_2_flag_opt` = R1、P4 の R2)・壊し patch、B-8 (10 s)。**未測は 3 経路:** P4 の留保 23 cell (条件は事前登録 §2 と D2223 項 1 で固定済みだが、測定は発効前)、mocc の性能規模 (動作点が未定)、TPC-C 段 1・段 2 の本番規模 (構成が未定) (§5)。
2. **既存の実測の最大は、巡回 0 で 3,275 万取引・辺 5.95 億・verify 896 s・node の増分 81.2 GiB (fixed-5 read-heavy 6 s)** である。これは観測した最大の規模であって、安全を保証する容量の境界ではない。新しい候補の取引数・辺数・グラフの形は、構成が同じでも既存の実測に含まれるとは限らない。
3. **設計 §6.1 の「read-heavy は 6 s まで」は狭すぎた。** B-8 本走 (2026-09-21) が read-heavy 10 s を 8 本、現行 verifier で完走させている (約 1,980 万取引・辺 3.47 億・verify 約 496 s)。同じ秒数でも build (候補) が違うと取引数が大きく違うので (どの flag が効いたかは分けていない)、範囲は秒数でなく取引数・辺数で読む (§3)。
4. **巡回の多い trace (設計 §6.2 の U1) を実測した。** 読み集合の再検証を外す壊し patch (norw) を性能構成の 3 workload で走らせ、同じ node・同じ configure の stock を対照にした。6 本とも完走し、norw 3 本の巡回は 472〜3,052 本 (stock 3 本は 0)、verify の総 wall を辺数で割った値は stock 比 −0.3〜+6.8 %、記憶量もほぼ同じだった (§4.2)。**段別の所要と強連結成分の統計は測っていないので、SCC の段が律速かどうかは判定していない。**
5. **参照 genome の 3 s trace を実測した。** R1 (`p2_2_flag_opt`) と R2 (rh の無 backoff) の Pegasus・trace 有効の走は記録が無かった。B0-L-W0 (wh / bal / rh) と B0-T-W0 (rh) の 4 本はすべて完走・serializable で、最大は B0-T-W0 の rh 1,668 万取引・辺 2.89 億・verify 420 s・node の増分 40.3 GiB (既存の fixed-5 rh 3 s とほぼ同じ規模) だった (§4.3)。
6. **[T-2351] を要する資源の超過は、取得した記録では観測されなかった。** 1 の実測はすべて完走し、node 全体の使用量を測った走 (容量 wave の改修版 14 走と本書の 10 走) では開始前を含む標本の最大が 86.2 GiB (容量 wave の rh6) で node の 115 GiB に届いていない (同じ compare の旧版 rh6 は 90.9 GiB で、これも届いていない)。ただし B-8 は verify process の RSS だけで node 全体を測っていない。「巡回の多い trace で SCC が律速」は未判定のまま (4 の理由)。再判定の条件は §5。

## 2. VLDB の実験が verify する trace (計算なし、2026-09-23 の main で棚卸し)

| 検証の経路 | extime | thread | workload / genome | 根拠 | 状態 |
|---|---:|---:|---|---|---|
| 合成ループの毎回検証 (既定の legacy) | 1 s | 4 | 200 レコード・読み 50 %・rmw・max_ope 5 | `orchestrator/campaign/pipeline.py` の `CorrectnessWorkload`、`loop.py` の `_closed_verify_workloads` | 現行コード、常時。B-10 正式走などの legacy 検証もこの構成 |
| S2 verify (opt-in) | 3 s | 48 | 100 万レコード・skew 0.9・rmw なし・max_ope 10・**読み 50 % 固定** | `pipeline.py` の `S2_FLAGS`・`s2_correctness_workload` | 現行コード、`legacy+s2` の campaign だけ |
| 性能構成 verify (opt-in) | `PerfConfig.extime` (既定 3 s) | `PerfConfig` の値 (錨は 48) | `PerfConfig.workload` をそのまま引き継ぐ (錨は読み 5 / 50 / 95 %) | `pipeline.py` の `performance_correctness_workload` | 現行コード、`legacy+performance` の campaign だけ |
| P3 の比較基盤 (D2220) | 3 s | 48 | 性能構成の錨。参照 `p2_2_flag_opt` も同じ correctness 条件で fresh に測る (D2220 項 3) | D2220、`output/insights/2026-09-22/t2849-comparison-harness-design/README.md` | 設計のみ |
| silo-function-policy 段 C / 段 D (D2214、D2226) | 1 s と 3 s | 4 と 48 | legacy と性能構成 | D2214 項 7、D2226、`output/insights/2026-09-22/t2857-silo-policy-stage-c/README.md` | 段 C は実測済み、段 D は設計のみ |
| D2160 の検証相 (採用静的 backoff 2 genome) | 3 s | 48 | fixed-5 / fixed-10 × 3 workload | D2160、`docs/paper-story/results/2026-09-20-verify-phase-adopted-backoff.md` | 実施済み |
| B-8 (最終候補の長時間検証) | 本走 10 s (校正は 6 / 10 s) | 48 | 案 A の S-1 最終候補 × 3 workload | D2202、`output/insights/2026-09-21/t2807-b8-effective/README.md` | 実施済み (判定集合 30 verify = 本走 24 本 (10 s) + 校正 6 本 (6 s 3・10 s 3)) |
| P4 の錨と比較対象 (D2223) | 3 s | 48 | 錨 = 性能構成。比較対象 R0 (上流既定 stock、BACK_OFF=1)・R1 (`p2_2_flag_opt`: wh / bal は B0-L-W0、rh は B0-T-W0)・R2 (wh 固定 10・bal 固定 5・rh 無 backoff = B0-L-W0 と同じ flag)・各手法の選択結果 | `docs/unseen-condition-transfer-preregistration.md` §2.1・§4 | 事前登録のみ、測定の発効は別決定 |
| P4 の留保 23 cell | 3 s | 17 cell は 48、6 cell は 12 / 24 | 1 因子ずつ: 読み 25 / 75 %、skew 0.7 / 0.99、thread 12 / 24、max_ope 5 / 20、rmw | 同 §2.2〜§2.3 | 同上 |
| mocc の性能規模 | 未定 | 未定 | 未定 | D2220 項 6 (pin の前進待ち) | 未定 |
| mocc の正例・負例 ([T-2844]) | 1 s | 1・4 | 200 レコード・読み 0 %・rmw | `orchestrator/campaign/s3_mocc_lock_coverage.py` | 実測済み (小構成) |
| TPC-C 段 1 (NewOrder / Payment) と段 2 (全 5 取引・範囲読み) ([T-2854]) | 未定 | 未定 (少 thread から) | 段 1 と段 2 で trace 量と verify の処理が違う (段 2 は述語処理が加わる) | `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §7.3〜§7.4 | 設計の試算のみ。段 1 の確認走 (1 s・2 thread・1 倉庫、36,156 取引) は `output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md` の表 (TPC-C B0 の行) |

- 差分分析の P3 (探索の独立反復) は verify 走の長さを書いていない。P3 は性能構成の点を使う設計 (D2220) なので、その行に含める。
- `orchestrator/campaign/silo_ladder_rung1.py` の 50 レコード・4 thread・1 s の verify は旧系列の段で、VLDB の実験の経路には入れていない。

## 3. 既存の実測範囲 (出所つき、いずれも巡回 0)

| 出所 | trace | 取引数 / 辺数 | verify wall | 記憶量 | 判定 |
|---|---|---|---:|---|---|
| 容量 wave (2026-09-20、`output/insights/2026-09-20/verifier-capacity/README.md` §4) | 14 本: fixed-5 の wh・bal 3 / 6 / 10 s と rh 3 / 6 s (8 本)、fixed-10 の wh・bal・rh 3 / 6 s (6 本) | 最大 rh6 32.75M / 594.8M | 最大 896 s | node の増分 (開始前からの差) 最大 81.2 GiB | 全件 serializable |
| B-8 本走 (2026-09-21、同上 t2807 §4、record は job dir `dev-wave-t2807-b8-effective/run/verify/*/rep-*/attempt-1/result.json`) | 案 A の S-1 最終候補、wh / bal / rh 10 s × 8 | wh 8.33〜8.42M / 85.1〜86.0M、bal 7.17〜7.32M / 103.0〜105.2M、rh 19.69〜19.95M / 345.3〜350.3M | wh 294〜297 s、bal 217〜222 s、rh 493〜501 s | verify process の最大 RSS: wh 15.3〜15.6、bal 15.9〜16.3、rh 48.0〜48.6 GiB | 24 件 serializable・certified |
| B-8 校正 (同上 §3) | 同じ候補の 6 / 10 s × 3 workload | rh10 19.61M | 最大 491 s | (本書では未集計) | 6 件 serializable・certified |

- 記憶量の量が出所ごとに違う。容量 wave の「node の増分」は probe が開始前の使用量を引いた値、B-8 は verify process 1 本の `ru_maxrss`、本書 §4 は両方 (node の増分と親 process の最大 RSS) を載せる。
- B-8 の rh10 は約 1,980 万取引で、fixed-5 の rh6 (3,275 万) より少ない。同じ 3 workload・48 thread でも、別の build (候補) の別の走で、extime あたりの取引数が約 2.8 倍違った (fixed-5 rh3 の 3 s あたり 16.8M 対 B-8 rh10 の 3 s 換算 5.9〜6.0M。どの flag の差が効いたかは対照で分けていない)。
- trace を取る側の費用 (設計 §6.2 の U5): B-8 の record によると、job ごとに 1 回の build は 16.1〜16.2 s、依存物の取得 (hydrate) は 10.8〜11.0 s、1 反復あたりの bench は 10.3〜10.4 s、commit の数え直しは 7.1〜20.3 s、保全 (zstd) は 11.9〜29.8 s。**job の所要のうち verify が 85.3〜88.2 % を占める** (job ごとの `stage_wall_s.verify / job_wall_s`。rh の job 1 は 2,259.5 s 中 1,987.1 s)。集計は `raw/b8-stage-walls.txt`。

## 4. 本 wave の実測

### 4.1 方法

- 起動器: job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-verifier-capacity/` の `launch_capacity.v1.py` (sha256 `53c1bb7e…`、job A・B) と `launch_capacity.py` (sha256 `ace714e8…`、job C・D。v1 に `--genome` を足したもの)。Codex `role=author` が書き、fix 2 回 (scratch をローカル disk へ、genome 指定の追加)。repo には入れない。s2 driver (`orchestrator/campaign/s2_verify_calibration.py`) の下位関数 (`_run_once`、`_verifier_run`、`applied`、`_require_condition_gate`、`assert_pinned_clean`、`_assert_single_tenant`、`_preflight_condition_gates`) を独自の build / verify の手順から呼ぶ (`_broken_build_and_verify` そのものは呼ばない)。差し替えは `PIN` (← 現行 pin)、`CLK` (1800 → 2100。Pegasus の env_contract の値)、`GATE2_VERIFIER_WALL_S` (600 → 1800。B-8 本走と同じ)、compiler の参照、verifier の出力の受動保存だけ。verifier の判定・閾値・patch の当て方 (fuzz なし) は変えていない。起動器の rc=0 は測定の完了を表し、全件 certified を意味しない。
- build: 全 build が trace 有効の Release。job A・B は `STOCK_G` (BACK_OFF=1 ほか s2 driver の既定) の stock と、それに `patches/broken-silo-norw-validation.patch` を当て `-DIZANAGI_BREAK_NOREAD_VALIDATION=1` を足した norw の 2 本 (configure の差はこの 2 つだけ)。job C・D は `Genome("silo", …).cmake_defines()` の B0-L-W0 (BACK_OFF=0・NO_WAIT_LOCKING_IN_VALIDATION=1・NO_WAIT_OF_TICTOC=0・WAL=0) と B0-T-W0 (BACK_OFF=0・NO_WAIT_LOCKING_IN_VALIDATION=0・NO_WAIT_OF_TICTOC=1・WAL=0) を 1 本ずつ、patch なし。configure argv の全文は raw の `builds.*.configure_argv`。raw の build の `walltime_s` は condition gate などを含み、compile だけの時間ではない。
- 走: 性能構成 (100 万レコード・48 thread・skew 0.9・rmw なし・max_ope 10・extime 3・clocks_per_us 2100) を、読み 5 % (wh)・50 % (bal)・95 % (rh) で各 1 回。trace と build は計算ノードのローカル disk `/scr` に置き、verify は本番の CLI (`python -m verifier <trace> --json --quiet --protocol silo --expected-commits <n>`、`--lenient` なし、worker は既定の 16) を `/usr/bin/time -v` の下で走らせた。node の使用量 (MemTotal − MemAvailable) を 2 秒ごとに標本した。
- job: A = stock / norw × wh・bal (bnode005、2026-09-23 09:13〜09:17 JST、Elapse 237 S)、B = stock / norw × rh (bnode006、09:13〜09:18 JST、Elapse 328 S)、C = B0-L-W0 × wh・bal・rh (bnode005、PRR で 09:43〜10:01 の割当て待ちの後 10:01〜10:13 JST、Elapse 684 S)、D = B0-T-W0 × rh (bnode007、09:43〜09:51 JST、Elapse 472 S)。`_assert_single_tenant` はすべて通過。生の記録は `raw/cap-{A,B,C,D}-{capacity,meta}.json`、verifier の stdout 全文は job dir の `runs/cap-*/verifier/`。

### 4.2 巡回の多い trace (U1): norw と同じ node の stock

| workload | build | 取引数 | 辺数 | 判定 | 巡回 (`total_cycles`) | verify wall | 辺あたり | verify の最大 RSS | node の増分 | oom_kill |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| wh 3 s | stock | 1,118,765 | 10,574,026 | serializable | 0 | 36.10 s | 3.41 µs | 2.27 GiB | 2.13 GiB | 0 |
| wh 3 s | norw | 1,118,445 | 10,572,948 | non-serializable | 472 | 38.55 s | 3.65 µs | 2.28 GiB | 2.29 GiB | 0 |
| bal 3 s | stock | 1,578,168 | 20,801,195 | serializable | 0 | 45.36 s | 2.18 µs | 3.56 GiB | 3.52 GiB | 0 |
| bal 3 s | norw | 1,606,848 | 21,218,727 | non-serializable | 3,052 | 48.86 s | 2.30 µs | 3.60 GiB | 3.52 GiB | 0 |
| rh 3 s | stock | 5,508,379 | 84,613,581 | serializable | 0 | 127.34 s | 1.50 µs | 12.67 GiB | 12.21 GiB | 0 |
| rh 3 s | norw | 5,810,066 | 89,839,762 | non-serializable | 747 | 134.83 s | 1.50 µs | 13.83 GiB | 13.69 GiB | 0 |

- 「辺あたり」は verify の総 wall を辺数で割った値。norw / stock の比は wh +6.8 %、bal +5.6 %、rh −0.3 %。取引あたりでは wh 32.3 → 34.5 s/百万、bal 28.7 → 30.4 s/百万、rh 23.1 → 23.2 s/百万。**各 1 回の走で、揺れの幅は測っていない。** この差を巡回の費用とは呼ばない。
- 最大 RSS は s2 driver の `maxrss_gb` (`/usr/bin/time -v` の kbytes を 2^20 で割った値なので単位は GiB) で、verify の親 process 1 本の値。「node の増分」は 2 秒ごとの標本の最大から verify 開始直前の値を引いたもの。
- 報告された anomaly は norw の 3 本とも 20 件で、CLI の既定の報告上限 (`--max-report 20`) である。巡回の総数は `total_cycles`。
- (2) の wave が同じ driver の関数で得た bal の観測 (2026-09-23 08:48 JST に job dir `dev-wave-t2847-patch-verify/runs/s2-1/s2_broken_at_pin.json` を読んだ時点の値: norw 巡回 3,262・verify 48.7 s・3.6 GiB、CLK 1800、bench の wall 3.35 s) とも桁が合う。
- s2 driver の stock (BACK_OFF=1) は、fixed-5 / fixed-10 より 3 s あたりの取引数が少ない (bal 1.6M 対 4.3〜4.5M、rh 5.5M 対 15.4〜16.8M)。このため、この 6 本は既存の実測の最大よりずっと小さい。**示したのは、この規模では巡回の有無で verify の総所要が桁では変わらないことまでである。**

### 4.3 参照 genome (R1・R2) の 3 s trace

| workload | genome (P4 §4 の役) | 取引数 | 辺数 | 判定 | verify wall | 辺あたり | verify の最大 RSS | node の増分 | oom_kill |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| wh 3 s | B0-L-W0 (R1) | 2,337,600 | 23,094,119 | serializable | 78.02 s | 3.38 µs | 4.59 GiB | 4.60 GiB | 0 |
| bal 3 s | B0-L-W0 (R1) | 4,123,681 | 58,055,846 | serializable | 125.03 s | 2.15 µs | 9.13 GiB | 9.14 GiB | 0 |
| rh 3 s | B0-L-W0 (R2 の rh) | 16,526,511 | 285,696,207 | serializable | 417.81 s | 1.46 µs | 40.24 GiB | 39.86 GiB | 0 |
| rh 3 s | B0-T-W0 (R1 の rh) | 16,683,499 | 288,640,680 | serializable | 419.99 s | 1.46 µs | 40.63 GiB | 40.34 GiB | 0 |

- 既存の fixed-5 の 3 s (容量 wave: wh 2.53M / 25.1M・86 s、bal 4.45M / 62.9M・134 s、rh 16.82M / 291.2M・433 s・node の増分 40.8 GiB) とほぼ同じ規模である。各 1 回の走。
- 本書は throughput を比べない (trace 有効 build の正しさ専用走、規律 1)。取引数は verify の規模としてだけ使う。

## 5. 容量の実測表と、範囲外の扱い

| 検証の経路 (§2) | 同じ構成の実測 | 出所 | 処置 |
|---|---|---|---|
| 合成ループの毎回検証 (1 s・4 thread・200 レコード) | あり | 約 27 万取引・辺 180 万、verify 5.8〜7.2 s・0.42 GiB (巡回ありを含む)。(2) の wave の legacy 走 (job dir `dev-wave-t2847-patch-verify/runs/s2-1/s2_broken_at_pin.json`、08:48 JST に読んだ値) | 測らない |
| S2 verify・性能構成 verify の 3 s (P3・段 D・P4 の錨・D2160) | あり (stock・固定 backoff・参照 genome・壊し patch) | 巡回 0: 容量 wave の 3 s 6 本 (最大 rh3 16.82M / 291.2M、433 s、増分 40.8 GiB)、本書 §4.3 の 4 本 (最大 rh 16.68M / 288.6M、420 s、増分 40.3 GiB)。巡回あり: 本書 §4.2 (最大 rh 5.81M / 89.8M、135 s) | 測らない。新しい候補は取引数・辺数が既存と違いうるので、その verify の記録で規模を見る |
| B-8 10 s | あり (実施済み) | §3 | 測らない |
| P4 の留保 23 cell (3 s) | **なし** | 測定の発効は D2223 で別決定。thread 12・24 は取引数を減らす方向、max_ope 20 は取引あたりの辺を増やす方向、skew 0.7 は競合を減らして取引数を増やしうる。どの向きも模型の推測で実測ではない | P4 の測定走そのものが verify の wall と記憶量を記録する |
| mocc の性能規模 | **なし** | 動作点が未定 (D2220 項 6) | P2 が mocc の性能規模の走を決めたとき、その構成で測る |
| TPC-C 段 1・段 2 の本番規模 | **なし** | [T-2854] の設計 §7.4 は YCSB の単価からの比例試算だけ。段 2 は述語処理が加わり別の費用になる | [T-2854] の設計どおり、少 thread・短時間の最初の 1 走で trace 量と verify 時間を測る |
| fixed-5 の read-heavy 10 s (設計 §6.2 の U3) | なし・要らない | この長さを検証する実験が無い (D2160 は 3 s を選び、B-8 は案 A で 10 s を完走) | 測らない |

**[T-2351] について:** 上の実測はすべて完走した。node 全体の使用量を測った走 (容量 wave の改修版 14 走と本書の 10 走) の標本の最大は、開始前の使用量を含めて 86.2 GiB (容量 wave の rh6、増分 81.2 GiB・verify 896 s) で、node の 115 GiB に届いていない。B-8 は verify process の RSS (最大 48.6 GiB) だけで、node 全体は測っていない。巡回の多い trace での SCC 段の律速は未判定である。以上から、[T-2351] を今すぐ要する資源の超過は、取得した記録では観測されなかった。**再判定するのは、** 未測の 3 経路を測ったとき、または規模にかかわらず verify が時間・記憶量の上限を超えるか未完走になったとき (既存の最大を超える取引数・辺数が出たときも含む) である。

## 6. 限定・言わないこと

- verify の段別 (parse・辺の構築・再生・SCC) の所要と、強連結成分の数・最大の大きさは測っていない。現行 verifier はこれらを出力せず、取るには verifier の内部へ計時を差し込む必要がある (容量 wave の probe は旧版の内部に差し込む作りで、現行版には当てていない)。巡回の影響は stock との総所要の比でだけ見た。
- 各条件 1 回の走で、揺れの幅は測っていない。§4.2 の 5〜7 % の差を効果として主張しない。
- 既存の実測の最大は観測した最大であって、容量の保証ではない。「3 s なら範囲内」とも言わない。
- node の増分は 2 秒ごとの標本の最大で、瞬間の最大を取りこぼしうる。最大 RSS は verify の親 process 1 本の値で、worker の分を含まない。
- 本書は性能値を含まない (trace を有効にした build の正しさ専用走、規律 1)。
- 壊した build の検出の型の分類 (期待表との突合) は (2) の wave の担当 (`output/insights/2026-09-23/t2847-patch-verify/README.md`) で、本書は判定の値を容量の記録として写すだけである。

## 7. 段 6 レビューと対応

独立 read-only レビュー 1 本 (Codex) は NO-GO (must-fix 3・should 5・nit 1)。全件を real と裁定し、次のとおり直した。

| 所見 | 対応 |
|---|---|
| must-fix: 全経路の包含の断定 | §1 の 1・2、§5、§6 を「構成が決まった経路に同じ構成の実測がある」「観測した最大であって境界ではない」へ改めた |
| must-fix: SCC 非律速と [T-2351] 非発火の断定 | §1 の 4・6、§5 を「資源の超過は観測されなかった、SCC 段の律速は未判定」へ改めた |
| must-fix: 棚卸しの漏れ (P4 の 17 cell は 48 thread、参照 genome、TPC-C 段 2) | §2 に行を足し、参照 genome (R1・R2) は記録が無かったので計算ノードで 4 本測った (§4.3、job C・D) |
| should: verify の占有率 | 85.3〜88.2 % に訂正 (§3) |
| should: node の量の定義 | 容量 wave・B-8・本書の量を区別し、本書の表を増分に揃えた (§3、§4.2) |
| should: fixed-10 に 10 s 走は無い | §3 の構成を明記 |
| should: brief の 2.6 s・GB・関数名 | brief は job dir の作業記録なので改訂しない。本書では bench の wall 3.35 s・GiB・下位関数を呼ぶ作りを正しく書いた (§4.1、§4.2) |
| should: TPC-C 確認走の出所 | `t2854-tpcc-ccbench-v3` の表を出所として明記 (§2) |
| nit: wh norw の wall | 原値 38.55 s で書いた |

S2 と性能構成 verify の違い (S2 は読み 50 % 固定、性能構成は `PerfConfig` を引き継ぐ) と、`silo_ladder_rung1.py` の除外も §2 に書いた。

焦点再レビュー (Codex、read-only) は NO-GO で、前回 9 件は closed 6・partial 3・regressed 0、新しい所見は must-fix 2・should 4・nit 1。実測の集計 (§4.2・§4.3 の全列、B-8 24 本、容量 wave 14 本、Elapse の和) は再計算で一致し、費用の合計 (1.58 → 1.57) と本数の内訳は訂正した。全件を real と裁定し、次のとおり直した。

| 所見 | 対応 |
|---|---|
| must-fix: P4 の留保 23 cell を「構成未定」と書いた (条件は事前登録 §2・D2223 項 1 で固定済み) | §1 の 1 を「条件固定済み・発効前・未測」へ改めた |
| must-fix: node 115 GiB の非超過を全経路へ広げた (B-8 は process RSS で node 全体ではない) | §1 の 6 と §5 を、node 全体を測った走の標本最大 86.2 GiB (開始前込み) に限定し、B-8 は未計測と書いた。再判定の条件に「規模にかかわらず上限超過・未完走」を足した |
| should: 費用を初回・追加時に分ける | 冒頭の計算欄を 1.92 / 1.57 node 時間の 2 段に分けた |
| should: B-8 の 30 本の内訳 | §2 に本走 24 (10 s) + 校正 6 (6 s 3・10 s 3) と書いた |
| should: fragment の参照先 | worklog fragment の段 6 の記述を本節と合わせた |
| should: 2.8 倍を backoff の因果として書かない | §3 を「別の build の別の走で観測した比、どの flag が効いたかは未分離」へ改めた |
| nit: 巡回の範囲の対象 | §1 の 4 に「norw 3 本 (stock 3 本は 0)」と書いた |

partial 3 件のうち brief の訂正は、brief が job dir の作業記録なので改訂しない (本書で正しく書いた)。

3 巡目の焦点再レビュー (Codex、read-only) は **GO** (前回 7 件は closed 6・partial 1、must-fix 0)。86.2 GiB が容量 wave の改修版 14 走と本書 10 走での最大であること (旧版を含めると rh6 の 90.9 GiB)、1.92 / 1.57 / 2.83 / 3.08 node 時間、B-8 の本走 24・校正 6 の内訳を原データから再計算して一致。残った should 2 件 (86.2 GiB の対象版の明記、§1 の 3 に残った「backoff で」の因果表現) と nit 1 件 (本節の要約の限定) は文言を直して閉じた。

## 8. 工数

- 子: 段 1 の棚卸し (Claude Explore、sonnet) 1、段 6 の参照 genome の記録探し (同) 1、段 5 author (Codex gpt-6-astra / medium) 1、fix 2、段 6 review 1、焦点再レビュー 2。
- 計算: 冒頭のとおり 4 job、Elapse 合計 1,721 S。受入全走は worklog に記録する。
