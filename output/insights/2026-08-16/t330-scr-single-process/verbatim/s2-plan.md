## 結論 (X — 実装差分ゼロで再裁定)

現時点で claim・reservation を供給して `loop.run_campaign` まで完走した sanctioned caller がなく、DW-G04 を満たせない。加えて S4 単独では現在の残穴を閉じないため、Y は設計メモ止まりとする。

## R1 の生死 (根拠 file:line つき)

R1 は「発火条件を満たす caller がない」という限定では生存している。ただし親の caller 列挙は不完全である。

静的 AST 抽出では `campaign.loop.run_campaign` の production call は 12 ファイル、15 箇所で、既存の閉じた inventory と一致した (`orchestrator/tests/test_campaign.py:4720-4740`)。親の列挙にないのは次の 4 ファイル、6 call である。

- `orchestrator/campaign/p3_kickoff.py:111,118`
- `orchestrator/campaign/p3_s4_loop.py:951`
- `orchestrator/campaign/p3_s4_red.py:165,175`
- `orchestrator/campaign/s8a_trigger_sweep.py:464`

親が挙げた 8 ファイルは、`p2_2.py:144`、`sanity_silo.py:59`、`backoff_sweep.py:173`、`s6_sort_sweep.py:362`、`backoff_repro.py:113`、`p3_s4_loop_sort.py:325`、`p3_s4_loop_trigger_gating.py:595`、`demo.py:57,66` で正しい。

tracked PBS job script は 7 本あるが、いずれもこの 12 caller を起動しない。

- `floor_campaign.sh:962` は `s8b_floor_campaign.py` を起動する。同ファイル自身の別関数 `run_campaign` (`s8b_floor_campaign.py:4052,5114`) であり、`campaign.loop.run_campaign` ではない。
- 他は `orchestrator/calibrate.py` (`certify_calibration.sh:724`)、`pegasus_floor_scoping.py` (`floor_scoping.sh:307`)、`silo_ladder_rung1.py` (`silo_ladder_rung1.sh:541`)、`run_probe.py` (`smoke_probe.sh:112`)、`t126_driver.py` (`t126_qualification.sh:789`)、inline profiler 処理である。
- `tools/*.py` に direct caller はない。計算ノード dispatch も `tests` と `provenance` の閉集合だけであり、計測 submitter ではない (`tools/pegasus/dispatch_compute.py:3-6,54-79`)。

ただし「PBS script が一本もない」という絶対表現には例外がある。repo 外の `/work/1/SFC/tanab/dev-wave-jobs/2026-08-15_t1097-s8c-live-abc/live/live.pbs:145-154` は 8c supervisor を起動し、構造上は `p3_autonomous_workload_trial.py:2768-2770` → `:2629-2645` → `p3_s4_loop_trigger_gating.py:595` へ至る。しかし request `911106` は transport admission で停止し、role attempt 0、`run_campaign` 到達 0 だった (`output/insights/2026-08-15_t1097-s8c-live-abc/README.md:77-97`)。claim・reservation も供給しないため、R1 を殺す発火 caller ではない。

## S4 の設計妥当性 (根拠 file:line つき)

一律に cache root を `/scr` へ移す S4 は、現在の正しい最小設計ではない。

まず `buildcache.py:1550` は legacy `build()` の cache root である (`buildcache.py:1514-1524`)。Pegasus contract 付き経路は `pipeline.py:863-897` から `build_v2` を使う。床値側の durable root は `s8b_floor_campaign.py:1953` で、実際の `build_v2` 呼出しは `:2115-2125` にある。

v2 は次を既に束縛する。

- source、CCBench commit、trace、compiler、toolchain、site、dependency-prefix path、admission を pre-image に含める (`buildcache.py:750-770`)。
- contract SHA で namespace を分離する (`buildcache.py:1343-1350`)。
- cache hit 時に pre-image、admission、current source evidence、toolchain、binary SHA を再検証する (`buildcache.py:918-1005,1363-1382`)。
- D136 は admission を v2 pre-image・completion manifest・campaign identity・replay・selection に束縛した (`docs/decisions.md:6616-6628,6656-6659`)。

さらに床値 wrapper は依存を `/scr/<PBS_JOBID>` に作って `CMAKE_PREFIX_PATH` へ export し (`floor_campaign.sh:97-101,810-923`)、v2 はその ambient path を正準化して identity に入れる (`buildcache.py:1043-1066,1311-1315`)。したがって床値経路は durable cache root でも job ごとに digest が変わり、実質的に既に跨ジョブ cold である。

一方、identity で塞げない残穴はある。

- dependency は path だけで内容 hash がない。同じ durable path の headers/libs を job A と B の間で差し替えると、B が A の binary を hit し得る (`buildcache.py:1043-1066`)。
- toolchain identity は realpath と version 先頭行で、実行ファイル bytes の hash ではない (`buildcache.py:685-698`)。
- subprocess 環境は明示 prefix 時に `CMAKE_PREFIX_PATH` を除く以外は継承するため、`CFLAGS`、`CXXFLAGS`、`LDFLAGS` などは identity 外である (`buildcache.py:1412-1429`)。
- WAL は binary SHA、cache-hit、configure/build command を残すが、full v2 pre-image、dependency bytes、build job identity は残さない (`pipeline.py:904-913`)。
- D136 自身も同一 process 発行器の真正性などには security credit を与えていない (`docs/decisions.md:6650-6654`)。

ただし fresh `/scr` は、同一 job 内の依存差替え、未束縛 ambient 入力、同一 UID による偽 completion entry、durable proof 欠落を閉じない。固定・不変な prefix を使う正当な v2 consumerでは毎 job rebuild にするだけである。必要なのは一律 cold 化ではなく、dependency/toolchain bytes の immutable manifest と、その full digest・build receipt の durable WAL/proof 束縛である。

## 裁定へ返す文面の骨子 (X のときのみ)

1. 失効した前提: 床値経路には claim root provisioning、reservation export、`/scr` TMPDIR、sink-local claim が既にある (`submit_floor.sh:403-432`、`floor_campaign.sh:716-740`、`s8b_floor_campaign.py:4236-4273`)。また「durable cache の跨ジョブ再利用は無条件に汚染」という前提も、v2 identity と D136 により宣言済み入力については失効した。

2. 生きている前提: tracked な `loop.run_campaign` 用 PBS wrapper と成功 measurement ID はない。`AcquiredClaim` は今も public constructible (`campaign_claim.py:62-68`) だが、現行 production sink は戻り値を権限として受け取らず acquisition の副作用だけを使う (`s8b_floor_campaign.py:4253-4263`)。したがって R2 は「caller から claim object を受け取る設計」を再採用した場合だけ発火する。R3 は実在し、Python 側は PBS job ID と boot ID を検査する一方、現在 hostname、script SHA、nonce authority を照合しない (`reservation.py:218-270`)。

3. 代替として必要なもの: まず 8c でない機械 worker を対象にするか、8c transport を使うかを再裁定する。前者なら実 caller と liveness measurement IDを先に作る。後者は D125 決定 (6) の scope を明示的に変更してから扱う。single-process は caller 提供の `AcquiredClaim` を受け取らず sink-local acquisition とし、reservation は owner-only create-only artifact、現在 host、job ID、boot ID、script hash、nonce、予算式をまとめて検証する。

4. DW-G04: 現在書ける `911096` / `911104` は configure probe にすぎず、`build_v2`、claim、reservation、loop を通していない。同 `911106` は 8c の admission failure である。したがって発火条件を満たす既存 artifact path または計測 ID は書けず、Y は設計メモ止まりとする。

5. 成果物影響: X では certified 選択、レポート、proof chain、受理集合、凍結 bytes はすべて変わらない。将来 non-8c trigger worker が走っても増えるのは Pegasus tagged の exploratory WAL・provenance・binary SHA であり、floor 認証選択とその proof chain は変わらない。

## 残るリスクと未検証点

D108 決定 (1) の計算ノード role 禁止は D122 により明示的に supersede 済みである (`docs/decisions.md:4983-4987,5878-5920`)。生きているのは D108 決定 (3) の `campaign` task 凍結と D125 決定 (6) の T-277 scope 境界である。さらに現在の phase doc は 8c live pilot を主経路に置く (`docs/phase3.md:496-503`) 一方、過去のユーザー裁定は D122 opt-in を「残すが使わない」としている。この不整合も T-330 で暗黙に解いてはならない。

調査は静的読解だけで、pytest、build、Pegasus 計測は実行していない。repo 外 `live.pbs` の存在と内容は確認したが、外部 artifact の完全な履歴・権威性は未検証である。

## 総括

X。R1 は sanctioned な発火 caller 不在という限定で生存するが、親の direct caller 列挙には 4 ファイルの漏れがある。  
S4 の一律 `/scr` 化は v2 identity と重複し、残る provenance 穴も閉じない。  
有効な計測 IDがなく DW-G04 を満たせないため、差分ゼロで caller 所有、8c 境界、immutable build provenance を再裁定へ返す。