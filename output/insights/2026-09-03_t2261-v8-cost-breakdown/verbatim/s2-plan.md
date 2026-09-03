## 1. 費用項の全列挙と分類

結論から言うと、`run_campaign()` の費用は単純な `F + nR` ではない。正常・fresh・`do_bench=True` の代表経路なら近似できるが、`settle()`、build cache、WAL 履歴、失敗による短絡が条件依存である。

### per-run 固定費 F

| 費用項 | 根拠 | 分類上の注意 |
|---|---|---|
| 引数・protocol shape・trigger marker・balanced schedule の事前検査 | [loop.py:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:270)-375 | F。失敗すれば以後は走らない |
| verify mode の解決、build policy の identity 束縛 | [loop.py:372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:372)-377、[loop.py:149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:149)-158 | F |
| writer authorization、environment contract 照合 | [loop.py:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:161)-178、[execution_guard.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/execution_guard.py:107)-145 | F |
| Pegasus calibration artifact 読込、live attestation、receipt 生成 | [loop.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:179)-193、[env_attestation.py:1028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/env_attestation.py:1028)-1041、[execution_guard.py:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/execution_guard.py:576)-624 | Pegasus では F、linux-baremetal では軽い別経路 |
| campaign identity 再計算 | [loop.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:194)-196、[ident.py:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/ident.py:226)-235 | F |
| reservation env 読込・job/boot/deadline 検査 | [loop.py:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:198)-207、[reservation.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/reservation.py:159)-175、[reservation.py:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/reservation.py:223)-275 | `single_process=True` の環境だけの F |
| claim root 検査、write capability、protocol digest、campaign claim 作成・fsync | [loop.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:208)-229、[campaign_claim.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/campaign_claim.py:383)-468 | F。ただし claim 全件走査があり、既存 claim 数で増えるので定数ではない |
| perf availability preflight | [loop.py:387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:387)-393、[loop.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:108)-146 | `do_bench=True` のときだけ F。`perf` と policy の2候補を順に probe し、各 timeout は10秒なので静的最悪上限は約30秒。[perf_preflight.py:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/calibrator/perf_preflight.py:100)-176 |
| layout の生成 | [loop.py:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:394)、[layout.py:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/layout.py:226)-230 | F。33 run なら33 layout |
| campaign lock 取得・解放 | [loop.py:396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:396)-404、[lock.py:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/lock.py:72)-89 | F |
| campaign.lock 照合、WAL tail repair、incomplete attempt recovery | [loop.py:405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:405)-425、[ident.py:472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/ident.py:472)-508 | 呼出しは一度だが、既存 WAL の長さ・未終端 attempt に依存 |
| WAL 全 replay、terminal/retryable 集合構築 | [loop.py:426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:426)-455、[wal.py:2646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/wal.py:2646)-2651 | 呼出しは F。ただし走査量は既存 WAL サイズ依存 |
| summary、`done`、`first_bench` 初期化、終端 log、return | [loop.py:457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:457)-465、[loop.py:652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:652)-654 | F |

Python process 起動・module import は `run_campaign()` の外である。[loop.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:12)-50 は import-time 費用だが、33 回の関数呼出しを同一 process で行えば1回しか払わない。これは F ではなく、別項 `J_process` とすべきである。

`settle()` も純粋な F ではない。

- `first_bench=True` は run ごとに初期化されるが、False になるのは最初の成功した bench 後だけである。[loop.py:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:463)、[loop.py:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:624)-629
- 実呼出しは bench に到達したときだけである。[pipeline.py:765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:765)-792
- 初回1回に加え、高CVで再測定すれば追加 round の前にも呼ぶ。既定3 round なら最大3回である。[stability.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/calibrator/stability.py:58)-90
- 1回の上限は20秒。[runner.py:271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/calibrator/runner.py:271)-290
- `do_bench=False`、または verify 前 abort なら0回である。

したがって `S_run` という条件付き項へ分離すべきである。

### per-row 変動費 R

| 費用項 | 根拠 |
|---|---|
| compiler 選択、source evidence の第一解決 | [loop.py:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:466)-486 |
| identity-error 時の build_start/abort WAL | [loop.py:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:487)-520 |
| `variant_id`、`done` lookup、duplicate skip | [loop.py:522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:522)-529 |
| evaluate 引数・trigger source binding の組立て | [loop.py:530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:530)-592 |
| perf receipt 再検証 | [pipeline.py:1806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1806)-1831 |
| per-evaluation authorization の再検査 | [pipeline.py:1030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1030)-1036 |
| source evidence の第二解決・caller 値との比較 | [pipeline.py:1079](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1079)-1110 |
| capability resolver、build admission 導出・検査 | [pipeline.py:1111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1111)-1129 |
| trigger predicate の source 読込・byte一致検査 | [pipeline.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:87)-119、[pipeline.py:1137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1137)-1164 |
| trigger binding・build_start WAL | [pipeline.py:1165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1165)-1178 |
| trace build と perf build の2本 | [pipeline.py:1197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1197)-1263 |
| cache hit の完全性検査、または configure/build/publish | [buildcache.py:2527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/buildcache.py:2527)-2639、[buildcache.py:3131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/buildcache.py:3131)-3303 |
| build_done WAL、binary/site gate | [pipeline.py:1315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1315)-1350 |
| 各 correctness repetition の tempdir、trace binary 実行、stdout parse、C行再計数 | [pipeline.py:1365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1365)-1470、特に [pipeline.py:420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:420)-443 |
| verifier、receipt capability、verify_done WAL | [pipeline.py:1471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1471)-1517 |
| correctness repetition loop | [pipeline.py:1521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1521)-1530 |
| full-scale S2 の bench lock・競合 process probe | [pipeline.py:1593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1593)-1633 |
| throughput bench の tempdir、lock、競合 probe、`measure_point`、再測定、解析、bench_done WAL | [pipeline.py:685](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:685)-877、[pipeline.py:1679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1679)-1711 |
| 各 bench round 内の `perf.extime × perf.reps` 個の subprocess | [runner.py:1057](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/calibrator/runner.py:1057)-1162 |
| commit receipt、site gate、commit WAL | [pipeline.py:1714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1714)-1773 |
| summary への結果・count 反映 | [loop.py:617](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:617)-629 |

R は同一値ではない。特に fresh build/cache hit、commit 数、verifier 入力量、再測定 round 数、どの段で abort したかで大きく変わる。

## 2. V-8 (a) で実際に33回払う項

### 33回になるもの

(a) が33個の fresh campaign identity を作るなら、上記 F の authorization、Pegasus attestation、reservation check、claim、perf preflight、layout、campaign lock、WAL identity/replay、summary は33回である。

`do_bench=True` で全行が正常に bench へ達するなら、初回 `settle()` も各 run で有効になり、少なくとも33回になる。高CV再測定まで含めると最大99回である。したがって「run あたり必ずちょうど1回」は誤りである。

### R 側にも差が出る

差は F だけではない。現行 (b) は33件を物理実行しない。

`variant_id` は genome と `src_token` だけで決まり、query ordinal、replicate ordinal、trigger nonce は含まない。[pipeline.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:121)-127

source mask と同じ validation mask は同じ materialized source/genome になるため、2件目は [loop.py:522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:522)-528 で skip される。支払うのは compiler/source 解決と `done` lookup までで、build・verify・bench は払わない。

したがって §5.3 の意味上の記述は現行実装と一致する。ただし同節の `loop.py:242-246` という行番号は古く、現行位置は `522-528` である。[phase3-8c-wiring-design.md:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/phase3-8c-wiring-design.md:367)-380

### build cache は run を跨ぐか

跨ぐ。cache identity に campaign ID は含まれない。

- legacy key は genome、CCBench commit、trace bit、`src_token`、compiler、build-admission receipt である。[buildcache.py:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/buildcache.py:624)-642
- v2 key はさらに toolchain manifest、site、dependency prefix、admission、environment contract namespace、任意の source snapshot・compiler-input・FetchContent binding を含む。[buildcache.py:1295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/buildcache.py:1295)-1384、[buildcache.py:2527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/buildcache.py:2527)-2554
- cache root は caller が固定でき、省略時も CCBench 下の `build-variants` である。[pipeline.py:1213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1213)-1223

ただし32 mask は source bytes、従って `src_token` が異なるので、通常は各 mask について trace/perf の fresh build が要る。source と同 mask の validation だけは内容が同一だが、source側が human-reviewed/coder-authored、validation側が machine-generated など admission body が異なれば key も異なり miss する。[build_admission.py:615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/build_admission.py:615)-675

さらに正式 S8b materialization は一意 worktree の絶対 `source_root` を admission preimage に含めるため、現行説明自身が「正式経路では cache hit は起きない」と明記している。[buildcache.py:2312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/buildcache.py:2312)-2318

よって「cache は campaign 横断可能」は real だが、「33行で広く hit する」は未成立である。

### 1 reservation で33 run を連続実行できるか

できる。33 scheduler jobs は要求されていない。

Pegasus binding は job ID・host・boot ID・deadline を表し、同じ job 内の各 `run_campaign()` が同じ環境変数を再検査できる。[reservation.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/reservation.py:26)-55、[reservation.py:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/reservation.py:223)-275

現状の `run_campaign()` が要求する残時間は各呼出しでわずか `required_s=1` であり、33 run の累積所要を予約検査していない。[loop.py:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:198)-207。したがって外側 controller が十分な walltime を要求する責任は残る。

claim は campaign identity ごとの one-shot file で release APIを持たない。[campaign_claim.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/campaign_claim.py:74)-79、[campaign_claim.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/campaign_claim.py:383)-400。33個の異なる campaign identity/protocol digest なら、同じ process・同じ reservation 内で順次取得できる。同じ campaign identity を再度呼ぶと既存 claim の `O_EXCL` で拒否される。[campaign_claim.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/campaign_claim.py:421)-434

従って scheduler 投入費の33倍は V-8 (a) の必然ではない。「33倍」を駆動し得るのは per-run attestation/preflight/settle/layout/claim であり、reservation job 数ではない。

## 3. 33行がどの protocol で走るのか

### 確定している部分

- source 1行 + mask `0..31` の32行、合計33 member、validation replicate は mask ごとに1。[phase3-8c-wiring-design.md:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/phase3-8c-wiring-design.md:339)-347
- 順序は source、その後 mask 0→31。[phase3-8c-wiring-design.md:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/phase3-8c-wiring-design.md:349)-360
- workload、environment、verifier policy は source origin/capability と一致しなければならない。[phase3-8c-wiring-design.md:268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/phase3-8c-wiring-design.md:268)-280
- formal holdout は H1=`rr80`、H2=`rr20`、skew 0.9、rmw 0、1M records、48 threads。[phase3-8b-descriptor-design.md:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/phase3-8b-descriptor-design.md:108)-118、[s8b_holdout_freeze.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/s8b_holdout_freeze.py:88)-104
- trigger driver の correctness mode は `legacy+S2`。[p3_s4_loop_trigger_gating.py:583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/p3_s4_loop_trigger_gating.py:583)-600
- legacy verify は tuple 200、thread 4、rr50、rmw=true、max_ope 5、extime 1、1 rep。[pipeline.py:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:130)-137
- S2 verify は tuple 1M、thread 48、rr50、rmw=false、max_ope 10、extime 3、1 rep。[pipeline.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:139)-164

### 未確定の部分

批准済み P6 protocol としての extime、performance reps、`do_bench` は未確定である。

現行 8c helper は formal H1/H2 についても performance を `extime=1, reps=2` にする。[p3_autonomous_workload_trial.py:804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/p3_autonomous_workload_trial.py:804)-816。一方、trigger-gating 偵察は `1M/48/extime3/reps5` である。[s8a_trigger_sweep.py:303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/s8a_trigger_sweep.py:303)-307、[p2_2.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/p2_2.py:53)-57。runbook が `100k/4/extime1/reps2` と確定するのは exploratory A/B/C pilot だけである。[phase3-s8c-autonomous-trial-runbook.md:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/phase3-s8c-autonomous-trial-runbook.md:142)-157

事前登録は extime/reps を後続再凍結で充填すると明記している。[phase3-8b-descriptor-design.md:322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/phase3-8b-descriptor-design.md:322)-345。8c の数値欄も未記入である。[phase3-8c-preregistration.md:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/phase3-8c-preregistration.md:194)-206。

また P6 は通常 verifier を必須にするが、throughput bench を必須とはしていない。[2026-08-03_t244-p6-contract/README.md:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/output/insights/2026-08-03_t244-p6-contract/README.md:301)-305。`do_bench=False` でも pipeline は verified commit を作れる。[pipeline.py:1728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/pipeline.py:1728)-1737。

最後に、33行 producer 自体がまだ存在しない。[phase3-8c-wiring-design.md:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/phase3-8c-wiring-design.md:379)-380、[phase3-8c-wiring-design.md:574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/docs/phase3-8c-wiring-design.md:574)-578。

従って、現在確定できる R は次の帯である。

1. correctness-only 帯: fresh/cache build + legacy 1 rep + S2 1 rep + commit、bench/preflight/settleなし。
2. current-8c surrogate 帯: 上記 + H1/H2 の extime1×2 reps bench。
3. 偵察/B-10型上側帯: extime3×5 reps。ただし批准済み P6 protocol とは呼ばない。

## 4. 親が実際に取るべき測定手順

### A. checkout と観測 regime を先に固定する

login node だけで完結し、新規投入は不要。

各 WAL について以下を必ず記録する。

- `source_commit`
- CCBench commit
- environment/host/PBS request
- workload flags、records、threads
- correctness tags と reps
- bench extime/reps
- build cache hit/miss
- 各 verify repetition の commit 数帯

B-10 `e3de15eb` は request `965564.nqsv` の `source_commit=0a07481…` であり、現 HEAD `c7ed565…` ではない。現行 verifier 並列化はその後の `d719c1e35`、`da45b6b2b`、`76b824f94` で入っている。この旧 WAL の R は verifier 部分について大きい側へ寄る。T-2191 の2.2倍は共有 login node・68万 txn 合成 trace の検査器単体値であり、end-to-end R 全体を2.2で割ってはならない。[t2191 README.md:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/output/insights/2026-09-02_t2191-verifier-parallel/README.md:99)-133、[同:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/output/insights/2026-09-02_t2191-verifier-parallel/README.md:164)-180

確認コマンドは次で足りる。

```bash
T2261_SOURCE=$(jq -r .source_commit <job-result-or-submit-receipt.json)
git cat-file -e "${T2261_SOURCE}^{commit}"
git diff --stat "$T2261_SOURCE"..HEAD -- \
  orchestrator/campaign/loop.py \
  orchestrator/campaign/pipeline.py \
  orchestrator/campaign/buildcache.py \
  orchestrator/verifier
```

### B. 現行コードの R を既存 WAL から分解する

login nodeだけ。新規投入不要。

最優先は既存の balanced campaign `143a3f74` である。submission `c42191…` の receipt は `source_commit=c7ed565892…`、すなわちこの worktree の HEAD と一致している。この campaign の `performance` repetition は rr50/1M/t48/extime3 なので、現行 S2 と同じ動作点である。検査時点ではまだ partial だったため、terminal 後に集計する。

```bash
T2261_WAL=/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-balanced-formal-143a3f74/runs/wal.jsonl

jq -s '
  sort_by(.variant,.ts)
  | group_by(.variant)[]
  | sort_by(.ts) as $r
  | range(1; $r|length) as $i
  | {
      variant: $r[$i].variant,
      from: $r[$i-1].stage,
      stage: $r[$i].stage,
      tag: ($r[$i].payload.workload.tag // null),
      dt_s: ($r[$i].ts-$r[$i-1].ts),
      bench_wall_s: ($r[$i].payload.bench_wall_s // null),
      trace_cached: ($r[$i].payload.trace_cached // null),
      perf_cached: ($r[$i].payload.perf_cached // null),
      commits: ($r[$i].payload.commits // null)
    }
' "$T2261_WAL"
```

読む量は次のとおり。

- `build_start → build_done`: trace+perf build/cache検査
- `build_done/verify_done → verify_done`: 1 correctness repetition の混合区間
- 最終 `verify_done → bench_done`: settle・lock・probe・bench・WAL
- `bench_done.payload.bench_wall_s`: bench subprocess群だけの monotonic 時間
- 両者の差: settle+lock+probe+payload/WAL の上側見積り
- `bench_done → commit`: receipt/site/WAL terminal
- `build_start → commit`: 1行の end-to-end R。ただし source の第一解決より前は含まない

B-10 の WAL 時刻差は trace実行、flush、C行再計数、parse、verifier、tmpdir、WALを含む混合区間である。[b10 README.md:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/output/insights/2026-09-02_b10-trace-truncation/README.md:171)-187。「検査器単体」へ読み替えない。

### C. settle の実費を既存 multi-row WALから取る

login nodeだけ。新規投入不要。

同じ campaign の最初の成功 variantについて

```text
(最終 verify_done → bench_done) - bench_wall_s
```

を取り、2件目以降の同じ量の中央値との差を `S_initial` の推定値にする。これは lock/probe/WAL差を完全には除けないため、`settle-only` ではなく「初回 bench admission の増分」と記録する。

login node 上で `settle()` 自体を直接計時してはならない。load average の regime が計算ノードと異なり、倍率へ入れられない。

### D. build cache の実効確認

login nodeで WAL を読むだけ。

`build_done.payload.trace_cached/perf_cached` を、mask/source/admission class ごとに表にする。特に source と同 mask の validation について、次の4値がすべて同じか確認する。

```text
genome canonical
src_token
trace bit
build_admission_receipt_sha256 / v2 preimage
```

一致しなければ「同じ mask だから hit」と数えない。

### E. F の扱い

既存 WAL は最初の `build_start` より前を記録しないため、authorization、attestation、reservation、claim、perf preflight、layout/replay の合計 F を正確には分離できない。

scheduler start→最初の `build_start` は、job staging・checkout・driver preflight まで混ざるので F の上限にしかならない。新規 instrumentation なしに exact F は得られない。

新しい計算ノード投入をしても、33-row P6 producer が存在しない以上、正式な V-8倍率は測れない。既存入口による surrogate を増やすより、

- current `143a3f74` WAL の R
- `settle≤20秒`
- perf preflight の最悪約30秒
- scheduler→first-WAL の外側上限

で倍率帯を出す方が安い。帯が裁定を変えるほど広い場合に限り、P6 protocol と producer を先に裁定・実装する必要がある。既存 formal admission を迂回した測定は代替にならない。

## 5. 倍率の再計算式

まず共通 job/process 費を `J`、run固有費を `F_i`、条件付き settle/admission を `S_i`、各物理行の費用を `R_i` とする。

### (a)

1 job内で33 campaign runを連続実行する場合:

\[
C_a = J + \sum_{i=0}^{32}(F_i + S_i + R_i)
\]

33 jobs は必要ないので、scheduler費を `33J` としてはならない。

### 現行 (b)

source と同 mask の validation を `d`、その行が skip までに払う source-resolution 費を `D_d` とすると:

\[
C_b =
J + F_b + S_b + D_d + \sum_{i\ne d}R_i
\]

これは32物理行しか持たず、certifiable な比較対象ではない。正しい成果物1件あたりの費用という意味では、(b) は倍率比較不能である。

実費だけを比較し、`F_i=F`、`S_i` を F に包含、`R_i=R`、`D_d=D` と単純化すると:

\[
M_{\text{current}} =
\frac{J+33F+33R}{J+F+32R+D}
\]

R 支配ならおおむね `33/32` に近づくが、分母側は正しい33行成果物を生成していない。

### duplicate を実行できる反実仮想 (b*)

現行コードを変えて33行すべてを物理実行できると仮定した場合:

\[
M_* =
\frac{J+\sum_i(F_i+S_i+R_i)}
     {J+F_b+S_b+\sum_iR_i}
\]

さらに `J=0`、全 F/R 同質、settle差を F に吸収した場合だけ、

\[
M_* = \frac{33F+33R}{F+33R}
\]

になる。

したがって親 brief の式は、反実仮想の均質モデルとしては正しいが、現行 (b) の式ではない。また process/job共通費、cache/admission差、settle再測定も落としている。

## 6. 親 brief への攻撃

### P1 — refuted

[P1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/s1-brief.md:38) は「(b)でも33物理実行」とするが、現行 `done` は同一 source/mask の2件目を skip する。[loop.py:522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:522)-528

従って差は `32F` だけではなく、(a) は duplicate validation の build/cache検査・verify・benchも追加で払う。式も現行コードには適用できない。

### P2 — refuted

[P2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/s1-brief.md:42) の列挙は尽きていない。

- process/import は `run_campaign` 外であり、同一processなら33回払わない。
- environment attestation、reservation検査、claim root capability、identity binding、campaign lock、WAL repair/replay、verify-mode閉包が抜けている。
- `settle()` は0回、1回、または再測定込み複数回になり得る。
- generic `run_campaign()` に campaign終端 seal は存在しない。terminal は各 variant の commit/abortで、最後はlogしてreturnするだけである。[loop.py:652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/orchestrator/campaign/loop.py:652)-654

存在しない seal や同一processの import を F に入れると倍率を大きい側へ誤る。

### P3 — refuted（局所主張は一部 real）

[P3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/s1-brief.md:46) の数学的方向、「F一定なら R が小さくなるほど倍率は33側へ動く」は real である。

しかし全体命題は refuted。

- 2.2倍は検査器単体、共有 login node、68万 txn の観測であり、R全体でもH1/H2でもない。
- 68–75%は旧 read-heavy の傾きに対する割合であり、P6の固定S2 rr50へ一般化できない。[t2191 README.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/output/insights/2026-09-02_t2191-verifier-parallel/README.md:13)-33
- 32 mask は `src_token` が違うので、build cache は大半が miss する。
- 2.2をR全体へ掛けるとRを過小評価し、倍率を過大評価する。

### P4 — real

[P4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2261-v8-cost/artifacts/s1-brief.md:49) は正しい。P6 producerがなく、事前登録のextime/repsも未確定なので、現時点のRは protocol別の帯でしか書けない。

### scope・成果物・実測環境

- V-8自体を選ばず、費用材料だけ返す scope と、コード差分0の方針は妥当。
- 成果物には単一倍率ではなく、`correctness-only/current-8c-surrogate/偵察型` の3 regime と「formal P6 protocol未確定」を必須で書くべきである。
- login nodeで静的分類・WAL集計を行う方針は妥当。ただし login node で測った import/settle をPegasus Fへ入れてはならない。
- 「B-10正式WALからRを読める一次資料」という一般化は過剰。旧 `e3de15eb` は `0a07481…`、旧直列 verifier、`legacy+performance`、extime3/reps5であり、P6 Rの直接値ではない。
- 「23分」は検査器単体でなく混合区間で、上端は24.43分である。[erratum README.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2261-v8-cost/output/insights/2026-09-02_t2229-t2230-verify-cost-erratum/README.md:24)-49

## 総括

- 確定したのは、F/Rのコード上の全経路、cacheがcampaign横断可能だがkey条件付きであること、`settle()`が「必ずrun当たり1回」ではないこと、33 campaignを1 reservation内で連続実行できること、現行 (b) がduplicateをskipして32物理行になること。
- 未確定なのは、formal P6 validation の `do_bench`、extime/reps、cache admission identity、およびproducer不存在のための実際のFである。従って正式な単一倍率はまだ出せない。
- 親が最初に取るべき測定は、既存・現HEAD由来の balanced campaign `143a3f74` がterminalになった後、そのWALから current S2-equivalent repetition、build、bench、初回bench admission増分を分解すること。login nodeで完結し、新規投入は不要。
- 放置すると測定値を誤る brief の点は次のとおり。

  - (b)を33物理行として分母を作る → 分母を過大にし、倍率を小さい側へ誤る。
  - process/importや存在しない終端sealを33回のFへ入れる → 倍率を大きい側へ誤る。
  - 旧B-10 read-heavy/直列verifierをP6のRとして使う → Rを大きく、倍率を小さい側へ誤る。
  - 検査器2.2倍をR全体へ適用する → Rを小さく、倍率を大きい側へ誤る。
  - 32 maskでbuild cacheが広くhitすると仮定する → Rを小さく、倍率を大きい側へ誤る。
  - 33 campaignには33 scheduler jobsが必要と仮定する → (a)を大幅に過大評価する。

テスト・ベンチは実走していない。上記は静的検査と既存成果物の読取りだけに基づく。