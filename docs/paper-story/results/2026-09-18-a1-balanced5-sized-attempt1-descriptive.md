# A-1 balanced5 sized 本走 attempt-0001 の結果節 — 3 workload の登録済み解析は `resolved-above-floor` (符号 +/+/−)、非認証 lane の descriptive 出力 (2026-09-18)

**これは投稿本文ではない。** 論文の結果節・表・図・限定へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の既存の稿を改めるものではない。** A-1 の sized 本走について、本稿の前に results 系列の稿は無い
(`docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」の 3 件目 (2026-09-18) が attempt の完走を
指しているが、それは stale 注記であって結果節の材料ではない)。**本稿は版 (`2026-09-17.md`)・claim-evidence 稿・
stale 注記・記録 insight の記述を数値の出所にしていない。** 出所は §5 に挙げる一次資料 (公開 leaf の result.json /
receipt.json、campaign WAL、事前登録、policy、裁定) だけである。

**本稿が判定しないこと (最初に置く):** A-1 の充足、`formal=false` から formal への昇格、再投入、本走の再認可のいずれも
本稿は判定しない。認可はユーザー手番である (D2044 項 8、D2120 項 3)。本稿は「attempt-0001 が何を出力したか」を
一次資料から書き写す文書であり、「A-1 の値がある」と書けるかどうかは本稿の外の裁定に属する。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

- **1 attempt = attempt-0001** (study `paper-story-a1-20260901-balanced5-sized-v1`、投入 2026-09-18 06:30 JST、3 job
  `4939.nqsv` / `4940.nqsv` / `4941.nqsv`)。sized の attempt はこの 1 本だけで、再投入は行われていない (§2.5)。
- **3 workload × 各 30 対 × 2 arm** = 180 測定。3 workload は同じ study の中の独立した campaign (別 job・別 node) であり、
  **workload をまたぐ結論は作らない** (事前登録 §7.2、result.json `limitations` 4 項目め)。本稿の表が 3 行あるのは
  並記であって集計ではない。
- 本稿の「登録済み解析」とは、事前登録 (§1.1) と policy v3 が結果を見る前に固定した推定対象・区間・分類規則を、
  materializer が result.json へ書いた出力を指す。

### 0.2 書くもの

- 権威 bytes (公開 leaf の `result.json`) が持つ 3 workload の `statistics` (対差の算術平均、標本標準偏差、`h`、記述区間、
  `B`、baseline 平均、分類、`variance_plan_breach`) と、それを作った 30 対の生値 (§2.2)。
- 各 arm の 30 標本の記述 (§2.3)、campaign WAL の `verify_done` が記録した正しさの判定 (§2.4)、時系列 (§2.5)。
- 結果を見る前に固定していた条件 (§1)、図 (§2.6)、この結果が言わないこと (§3)、一次資料 (§5)。

### 0.3 書かないもの

- 研究として成功か失敗かの宣告 (D12)。3 workload の符号 (+ / + / −) を「採用静的 backoff の優劣」へ拡張すること。
- **headline 値としての採用。** この lane は `formal=false` / `promotion_prohibited=true` /
  `result_authority = sized-preregistered-descriptive-only` であり、policy と事前登録がその反転を文書編集で行うことを禁じている
  (事前登録 §7.2)。
- **C1 の再現判定。** 符号が C1 の旧環境値 (write-heavy +38.3% / balanced +11.3% / read-heavy −6.6%) と 3 workload とも一致する
  ことは観察であって再現判定ではない (推定対象・環境・分母の処理が異なる。D1993 と claim-evidence の `L23` の区別を維持)。
- **反復間の安定性への一般化。** 単一 attempt であり、attempt 間の再現性については何も言えない (§3 限定 4)。
- A-2 / A-6 / [T-1998] との集計 (D1993 項 6)、pilot の観測値の混入 (事前登録 §7.2)、機序の同定、他の CCBench pin・他の機体への転移。

### 0.4 主判定文 (結果節へ落とすときの形。文を分けたまま使う)

attempt-0001 の trace-disabled 性能測定では、登録済み解析の出力は 3 workload とも `resolved-above-floor` だった —
対差平均 (variant − baseline) は write-heavy +1,591,948.5 tps、balanced +448,830.17 tps、read-heavy −576,749.77 tps で、
各 workload の記述区間 (平均 ± h) は床 ±B の外にある。これは事前登録した分類規則の descriptive な出力であり、
仮説検定でも性能認証でもない。この lane は `formal=false` / `promotion_prohibited=true` のままである。
別の trace-enabled 走行では、6 arm とも `verify_done` が `certified=true` / `anomalies=0` / `verdict=serializable` と
記録されており、それは性能の判定ではない (§2.4)。

---

## 1. 条件 — 結果を見る前に固定したもの

### 1.1 事前登録と policy

- 事前登録: `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md`
  (sha256 `6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2`、policy の `preregistration` field が束縛)。
- policy: `orchestrator/campaign/paper_story_a1_paired.v3-sized.json` (`paper-story-a1-paired-policy/v3`、
  sha256 `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a`。result.json の `policy_sha256` と
  receipt.json の `policy.sha256` が同じ値を持つ)。
- `authority`: `formal=false`、`promotion_prohibited=true`、`result_authority="sized-preregistered-descriptive-only"`。
- 推定対象 (`pairing.estimand`): `arithmetic mean of paired differences under the balanced five-rep schedule`。
  contrast は `variant-minus-baseline`、配置は `balanced-a5b5-b5a5-v1` (10 対を 1 群とし、群ごとに seed から引いた
  1 bit で `A^5 B^5 B^5 A^5` か `B^5 A^5 A^5 B^5` の物理順を決める。A = variant、B = baseline)。
- 反復数: 3 workload とも `reps=30` (`df=29`)。`k = 2.8315526875186725` (`t(1 − (1/120)/2, 29)`、事前登録 §5.1)。
  `planned_sigma_tps` は write-heavy `66403.452108019716`、balanced `56697.435713574683`、read-heavy `74668.489566274948`
  (policy の文字列値。result.json は float 化した値を持つ)。
- 区間と床 (事前登録 §5.1): `h = k · s / √n` (`s` = 30 対の差の標本標準偏差)、区間 `[mean − h, mean + h]`、
  `B = (3/100) × (その workload の baseline 平均)`。
- 分類 (事前登録 §5.2 と実装): `abs(mean) − h > B` → `resolved-above-floor`、`abs(mean) + h ≤ B` → `bounded-below-floor`、
  それ以外 → `unresolved`。**事前登録 §5.2 の語 (`resolved-beyond-floor (improvement / regression)` /
  `bounded-within-floor`) と、実装・result.json の語 (`resolved-above-floor` / `bounded-below-floor`) は異なるが、
  述語は同値である** (`L > B` または `U < −B` ⟺ `abs(mean) − h > B`)。向きは平均の符号で読む。
  v3 の policy JSON は `classification_rules` を持たず、述語は実装 `orchestrator/campaign/paper_story_a1_paired.py` の
  `_classify_difference` にあり、`floor_fraction` は同 file の `_statistics_from_signed_differences` が v3 では定数
  0.03 として持つ (policy の `sizing.floor_fraction` 3/100 とは検証時に照合される)。k・df・`planned_sigma_tps` は
  policy の `workloads[]` にある。
- `variance_plan_breach`: `sample_sd > planned_sigma_tps` (事前登録の計画 sigma を標本 sd が超えたか。3 本とも false、§2.1)。
- pilot の観測値は反復数の決定にだけ使い、最終推定へは 1 点も入れない (policy `sizing_inputs`、事前登録 §7.2)。

### 1.2 arm と genome (policy `workloads[].arms`、campaign.lock の `identity_preimage`、WAL `build_start` と一致)

| workload | rratio | variant arm (minuend) | baseline arm (subtrahend) |
|---|---:|---|---|
| write-heavy | 5 | `fixed10`: `silo\|BACKOFF_FIXED=10,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` | `no-backoff`: `silo\|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| balanced | 50 | `fixed5`: `silo\|BACKOFF_FIXED=5,BACK_OFF=1,…` (他 3 flag は同じ) | 同上 |
| read-heavy | 95 | `fixed2`: `silo\|BACKOFF_FIXED=2,BACK_OFF=1,…` (他 3 flag は同じ) | 同上 |

variant の識別子 (WAL の `variant`): `fixed10` = `a7f8486e1116`、`fixed5` = `93c62227a2d3`、`fixed2` = `82ea3a7b8618`、
`no-backoff` = `84319b1127a6` (3 workload で共通)。静的 backoff は `patches/silo-backoff-fixed.patch`
(source binding の 1 本) が入れる枝であり、`BACK_OFF=0` の baseline はその枝も CCBench 内蔵の適応 backoff も持たない。

### 1.3 測定条件 (policy `scale` / `execution`、WAL `bench_done.run_cmd`)

- records 1,000,000、threads 48、`ycsb_zipf_skew` 0.9、`ycsb_rmw` 0、`ycsb_max_ope` 10、`extime` 3 s、`clocks_per_us` 2100、
  protocol silo、CCBench pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` (`ccbench_acceptance.canonical_pin`)。
- 実行の形: workload ごとに fresh な exact 2-arm campaign を 1 つ、両 arm の build と verify が終わってから bench、
  bench は 1 round (`bench_max_rounds` 1)、5-rep block ごとに競合テナント probe (fail-closed)、settle は workload schedule の
  開始時に 1 回、`site` は `pegasus-compute-only`、自動再試行なし。
- source: `measurement_source_commit = d2ebef7a407dc6be61622ed596cf08b8b518f606` (local main、投入 worktree は detached)。
  `source_binding.evidence_level = source-routed-trace0`、`artifact_standalone_proof = false` (成果物単独では build 経路を
  証明しない。束縛 file 9 本の blob oid と working sha256 は result.json `source_binding.files`)。
- perf は使っていない (`bench_done.perf_observation.use_perf = false`、`counter_status = not_required`)。
  leading indicator は throughput だけで、abort 率・latency・LLC・IPC は null。
- 正しさの検査条件 (`legacy`) は WAL の `verify_done.workload.tag` に `legacy` とだけ記録されており、その実引数
  (tuple 数・thread 数・rratio 等) は本 attempt の成果物には無い (§4.1)。

### 1.4 投入と受領証

- 裁定: D2120 項 3 (2026-09-17) が既存 submit 経路で 1 attempt を認可 (落ちたら再投入せず報告して止める)。
  D2044 項 8 / D1986 項 5 の据え置き条件は entry 1590 (commit `ad83b108b`) で成立。
- submit: `paper_story_a1_paired submit --study-id paper-story-a1-20260901-balanced5-sized-v1 --expected-head d2ebef7a4…`
  (2026-09-18 06:30:16 → 06:30:38 JST、rc 0)。route `direct-qsub-workload-fanout`、intent sha256
  `7eb404861e9a5336c6169445885a7083c12f801ade5068e9b1ad09ad025a2750`。
- job (receipt.json `job_executions` / `reservation_binding`): 3 本とも queue `gen_S`、`requested_s` 21600、
  job script sha256 `3c2b734d9c71caca583baa4fd950bb55957dc64e90b2c27ec8e60eb8705fed80` (= `tools/pegasus/paper_story_a1_paired.sh`)。

| workload | request | host | scheduler start (JST) | job end (JST) | elapsed s | CPU total s |
|---|---|---|---|---|---:|---:|
| write-heavy | `4939.nqsv` | bnode107 | 06:30:45 | 06:39:59 | 553.96 | 9121.249 |
| balanced | `4940.nqsv` | bnode108 | 06:30:45 | 06:43:20 | 755.30 | 9121.098 |
| read-heavy | `4941.nqsv` | bnode109 | 06:31:13 | 06:36:37 | 323.80 | 9118.327 |

(時刻は `accounting.started_epoch_s` / `ended_epoch_s` を JST へ換算。CPU は job body の Bash `times` の差分。)
- scheduler terminal: 3 本とも `request-disappeared-after-visibility` (投入時に `QUE` で可視、終端後の `qstat` が
  `does not exist` を返す形)。state / exit_status は「未観測」と記録され、成功は `driver_rc=0` / `shell_rc=0` /
  `status=finished` で独立に確定している (result.json `materialization_evidence.interpretation`)。
- complete: 06:44:13 → 06:44:28 JST (rc 0、completion 受領証 sha256 `d26c4852…`、group terminal sha256
  `c46ae55cd9be5866956d5ffdefe5b86326de5899e8aa611725d6cf51631bbd15`)。materialize: 06:45:00 → 06:45:38 JST (rc 0)。

---

## 2. 結果

### 2.1 登録済み解析の出力 (公開 leaf `result.json` の `workloads[].statistics` から逐語。descriptive のみ)

| workload | contrast | n | mean (variant − baseline) tps | h tps | descriptive interval tps | B tps | baseline mean tps | sample sd tps | planned sigma tps | classification | variance_plan_breach |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|---|
| write-heavy | `fixed10` − `no-backoff` | 30 | `1591948.5` | `23911.502943472762` | `[1568036.9970565273, 1615860.0029434727]` | `68795.219` | `2293173.966666667` | `46253.31396347129` | `66403.45210801972` | `resolved-above-floor` | `false` |
| balanced | `fixed5` − `no-backoff` | 30 | `448830.1666666667` | `28351.599461068836` | `[420478.5672055979, 477181.7661277355]` | `115876.89600000001` | `3862563.2` | `54842.032905228465` | `56697.43571357468` | `resolved-above-floor` | `false` |
| read-heavy | `fixed2` − `no-backoff` | 30 | `-576749.7666666667` | `32963.69867738655` | `[-609713.4653440532, -543786.0679892802]` | `310204.40199999994` | `10340146.733333332` | `63763.46597396226` | `74668.48956627495` | `resolved-above-floor` | `false` |

- `k = 2.8315526875186725`、`df = 29`、`floor_fraction = 0.03`、`pairing_design = balanced-a5b5-b5a5-v1`、
  `contrast = variant-minus-baseline` は 3 workload とも同じ (同 `statistics`)。
- `terminal_result` は 3 workload とも `{status: valid, classification: resolved-above-floor}`、`valid=true`、`errors=[]`。
  最上位は `complete=true`、`all_workloads_terminal=true`、`measurement_error=null`、`formal=false`、
  `promotion_prohibited=true`、`workload_reps` 30 / 30 / 30。
- **符号:** write-heavy 正、balanced 正、read-heavy 負。分類はいずれも「区間が床の外」を言うだけで、向きを持たない。
- **本稿の作成時に 30 対の生値から再計算した検算:** 3 workload とも `signed_difference_tps = <variant>_tps − no-backoff_tps` が
  全 30 対で完全一致、`pairs[i].<arm>_tps` が `arms.<arm>.raw_tps[i]` と一致、mean / `h` / `B` / 区間 / 分類が上の表と一致
  (`s` は最終桁の浮動小数点丸めの範囲で一致: write-heavy `46253.31396347129`、balanced `54842.03290522846`、
  read-heavy `63763.465973962266` を再計算値として得た)。標本 sd / 計画 sigma の比は 0.697 / 0.967 / 0.854 (本稿の派生値)。
- **派生値 (登録量ではない。読み手の目安であり、結果節の数値にはしない):** 対差平均 / baseline 平均 =
  write-heavy +0.694、balanced +0.116、read-heavy −0.056。この比の分母は baseline arm の 30 標本の算術平均で、
  A-2 / A-6 の `adopted_median / stock_median − 1` とも、[T-1998] の median 比とも定義が違う。

### 2.2 30 対の生値 (`statistics.pairs`。単位 tps。pair_index の順 = 物理順ではなく対の番号)

write-heavy (`fixed10_tps`, `no-backoff_tps`, `signed_difference_tps`):

| # | fixed10 | no-backoff | diff | # | fixed10 | no-backoff | diff | # | fixed10 | no-backoff | diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 3926656 | 2481442 | 1445214 | 10 | 3882434 | 2285777 | 1596657 | 20 | 3882354 | 2272458 | 1609896 |
| 1 | 3929996 | 2365221 | 1564775 | 11 | 3888281 | 2253680 | 1634601 | 21 | 3850724 | 2224397 | 1626327 |
| 2 | 3916390 | 2407240 | 1509150 | 12 | 3878410 | 2346151 | 1532259 | 22 | 3881145 | 2264264 | 1616881 |
| 3 | 3918147 | 2276044 | 1642103 | 13 | 3899804 | 2325755 | 1574049 | 23 | 3872280 | 2294309 | 1577971 |
| 4 | 3906234 | 2309222 | 1597012 | 14 | 3858848 | 2277190 | 1581658 | 24 | 3862447 | 2298790 | 1563657 |
| 5 | 3888481 | 2326735 | 1561746 | 15 | 3869692 | 2292397 | 1577295 | 25 | 3870225 | 2326580 | 1543645 |
| 6 | 3911088 | 2286334 | 1624754 | 16 | 3842760 | 2251860 | 1590900 | 26 | 3827850 | 2248395 | 1579455 |
| 7 | 3916988 | 2280104 | 1636884 | 17 | 3831594 | 2203616 | 1627978 | 27 | 3883667 | 2200172 | 1683495 |
| 8 | 3931043 | 2294703 | 1636340 | 18 | 3881225 | 2280571 | 1600654 | 28 | 3874270 | 2270283 | 1603987 |
| 9 | 3892826 | 2313058 | 1579768 | 19 | 3883187 | 2287548 | 1595639 | 29 | 3894628 | 2250923 | 1643705 |

balanced (`fixed5_tps`, `no-backoff_tps`, `signed_difference_tps`):

| # | fixed5 | no-backoff | diff | # | fixed5 | no-backoff | diff | # | fixed5 | no-backoff | diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4334831 | 4063471 | 271360 | 10 | 4307511 | 3858116 | 449395 | 20 | 4300638 | 3850903 | 449735 |
| 1 | 4312415 | 3971107 | 341308 | 11 | 4319967 | 3883242 | 436725 | 21 | 4311693 | 3776752 | 534941 |
| 2 | 4346490 | 3867152 | 479338 | 12 | 4318241 | 3830979 | 487262 | 22 | 4311261 | 3848680 | 462581 |
| 3 | 4357394 | 3981753 | 375641 | 13 | 4266203 | 3860745 | 405458 | 23 | 4295880 | 3832275 | 463605 |
| 4 | 4322303 | 3858817 | 463486 | 14 | 4297481 | 3844141 | 453340 | 24 | 4285548 | 3795857 | 489691 |
| 5 | 4334030 | 3912345 | 421685 | 15 | 4316059 | 3869901 | 446158 | 25 | 4283546 | 3829388 | 454158 |
| 6 | 4334403 | 3873261 | 461142 | 16 | 4293161 | 3791349 | 501812 | 26 | 4299755 | 3800446 | 499309 |
| 7 | 4350699 | 3849766 | 500933 | 17 | 4288795 | 3933144 | 355651 | 27 | 4288170 | 3861696 | 426474 |
| 8 | 4335013 | 3878068 | 456945 | 18 | 4296386 | 3792192 | 504194 | 28 | 4307154 | 3829792 | 477362 |
| 9 | 4333271 | 3883709 | 449562 | 19 | 4299540 | 3852899 | 446641 | 29 | 4293963 | 3794950 | 499013 |

read-heavy (`fixed2_tps`, `no-backoff_tps`, `signed_difference_tps`):

| # | fixed2 | no-backoff | diff | # | fixed2 | no-backoff | diff | # | fixed2 | no-backoff | diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 9850761 | 10605597 | -754836 | 10 | 9789429 | 10318105 | -528676 | 20 | 9761860 | 10264166 | -502306 |
| 1 | 9788490 | 10493554 | -705064 | 11 | 9769050 | 10329274 | -560224 | 21 | 9712352 | 10258699 | -546347 |
| 2 | 9779977 | 10472470 | -692493 | 12 | 9771090 | 10251908 | -480818 | 22 | 9737516 | 10336986 | -599470 |
| 3 | 9876628 | 10498728 | -622100 | 13 | 9764019 | 10355122 | -591103 | 23 | 9743014 | 10269106 | -526092 |
| 4 | 9756813 | 10315828 | -559015 | 14 | 9804220 | 10347940 | -543720 | 24 | 9695636 | 10308313 | -612677 |
| 5 | 9804611 | 10377673 | -573062 | 15 | 9827892 | 10359622 | -531730 | 25 | 9712880 | 10275959 | -563079 |
| 6 | 9800338 | 10309199 | -508861 | 16 | 9768523 | 10265695 | -497172 | 26 | 9730775 | 10345615 | -614840 |
| 7 | 9763660 | 10375610 | -611950 | 17 | 9690999 | 10350494 | -659495 | 27 | 9706841 | 10263100 | -556259 |
| 8 | 9731806 | 10326936 | -595130 | 18 | 9764561 | 10334679 | -570118 | 28 | 9732940 | 10269295 | -536355 |
| 9 | 9784457 | 10383227 | -598770 | 19 | 9760163 | 10283097 | -522934 | 29 | 9720608 | 10258405 | -537797 |

(値は result.json の float を整数表記にしたもの。全 180 標本が整数値である。)

### 2.3 arm ごとの 30 標本の記述 (`arms.<name>.raw_tps` から本稿が計算した派生値。WAL `bench_done` の `median_tps` / `cv` は記録値)

| workload | arm | mean tps (派生) | min / max tps (派生) | median tps (WAL) | cv (WAL、標本 sd / 平均) | unstable | rounds | attempts |
|---|---|---:|---|---:|---:|---|---:|---:|
| write-heavy | fixed10 | 3,885,122.47 | 3,827,850 / 3,931,043 | 3882810.5 | 0.007025408387754655 | false | 1 | 1 |
| write-heavy | no-backoff | 2,293,173.97 | 2,200,172 / 2,481,442 | 2286055.5 | 0.024522075963025195 | false | 1 | 1 |
| balanced | fixed5 | 4,311,393.37 | 4,266,203 / 4,357,394 | 4309386.0 | 0.005103266632077728 | false | 1 | 1 |
| balanced | no-backoff | 3,862,563.20 | 3,776,752 / 4,063,471 | 3855507.5 | 0.015976453757935626 | false | 1 | 1 |
| read-heavy | fixed2 | 9,763,396.97 | 9,690,999 / 9,876,628 | 9763839.5 | 0.004486330231750992 | false | 1 | 1 |
| read-heavy | no-backoff | 10,340,146.73 | 10,251,908 / 10,605,597 | 10328105.0 | 0.008054510418980403 | false | 1 | 1 |

- 6 arm とも `expected_reps = observed_reps = 30`、`actual_rounds = 1`、`attempt_count = 1`、`unstable = false`、
  `high_variance = false` (WAL `commit`)、`rep_notes = []`、`valid = true`、`errors = []`。品質 gate (`aggregate_cv > 0.05` で
  unstable) には 6 arm とも掛かっていない。
- baseline (`no-backoff`) の cv は 3 workload とも variant より大きい (0.0245 / 0.0160 / 0.0081 対 0.0070 / 0.0051 / 0.0045)。
  これは観察であり、本稿はその理由を述べない。
- median は 5 標本 median を使う A-2 / A-6 と形式が違う (30 標本の中央値、WAL の `median_tps`)。本稿の推定量は median ではなく
  対差の算術平均であり、arm 単体の median は結果節の数値にしない。

### 2.4 正しさの記録 — campaign WAL の `verify_done` (性能の判定ではない)

3 本の WAL (`runs/wal.jsonl`、各 10 record: `build_start` / `build_done` / `verify_done` × 2 arm、`bench_done` × 2、`commit` × 2)
の `verify_done` 6 record:

| workload | arm (variant id) | commits | aborts | anomalies | certified | verdict | check config |
|---|---|---:|---:|---:|---|---|---|
| write-heavy | fixed10 (`a7f8486e1116`) | 459238 | 107049 | 0 | true | serializable | `legacy` |
| write-heavy | no-backoff (`84319b1127a6`) | 544423 | 209963 | 0 | true | serializable | `legacy` |
| balanced | fixed5 (`93c62227a2d3`) | 466561 | 130497 | 0 | true | serializable | `legacy` |
| balanced | no-backoff (`84319b1127a6`) | 483318 | 185235 | 0 | true | serializable | `legacy` |
| read-heavy | fixed2 (`82ea3a7b8618`) | 516607 | 181083 | 0 | true | serializable | `legacy` |
| read-heavy | no-backoff (`84319b1127a6`) | 515988 | 196776 | 0 | true | serializable | `legacy` |

- `proof_surfaces` は 6 record とも `{protocol: silo, X: evidence-present, P: evidence-present, I: evidence-absent}`、
  `commit_witness.commit_counts` は `commits` と一致、`batch_commit_counts` 0。
- result.json 側は `arms.<name>.correctness_evidence = {certified: [true], verify_configs: ["legacy"], verify_done_frames: [1 件]}`
  で、frame の `raw_sha256` と byte range で WAL の該当行を束縛する (anomaly 数は result.json には無く、WAL だけが持つ)。
- **これは規律 2 の判定であって性能の判定ではない。** `certified` が言うのは、記録された `legacy` 検査条件の下で観測した
  YCSB point read/write trace の直列化可能性までであり、性能認証ではない。verify は trace-enabled build、bench は
  trace-disabled build で、別 build・別 run である (絶対規律 1)。
- **記録 insight の表との差:** `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md` §4 の表は balanced と read-heavy の
  commit 数を入れ替えて記載している (balanced に 516607 / 515988、read-heavy に 466561 / 483318)。WAL と同 insight の
  `receipts/job-stdout-{balanced,read-heavy}.txt` は上の表のとおりである。本稿は WAL の値を使う (insight は凍結記録なので
  書き換えない。この差は本稿を書いた wave の insight に観察として残す)。

### 2.5 時系列 (JST。WAL `ts`・receipt の epoch・成果物 mtime から換算。推定値なし)

| 時刻 | 事象 | 出所 |
|---|---|---|
| 06:30:16 → 06:30:38 | submit rc 0 (intent 06:30:36、submission 受領証 06:30:38) | 記録 insight §3 (mtime) |
| 06:30:45 / 06:30:45 / 06:31:13 | job 開始 write-heavy / balanced / read-heavy | receipt `accounting.started_epoch_s` |
| 06:31:42〜06:33:14 | 6 arm の build (各 17〜18 秒) と verify (各 12〜14 秒)。write-heavy: fixed10 verify_done 06:32:12、no-backoff 06:32:47。balanced: 06:32:12 / 06:32:45。read-heavy: 06:32:40 / 06:33:14 | WAL `ts` |
| 06:33:15 | bench-start barrier 3 本同時 (最後の ready barrier = read-heavy 06:33:15 の直後) | 記録 insight §3 (barrier file mtime) |
| 06:36:36 / 06:39:58 / 06:43:19 | bench_done と commit (read-heavy / write-heavy / balanced)。`bench_wall_s` は arm ごとに 100.4〜100.8 秒 | WAL `ts`、`bench_done.bench_wall_s` |
| 06:36:37 / 06:39:59 / 06:43:20 | job 終了 (read-heavy / write-heavy / balanced) | receipt `accounting.ended_epoch_s` |
| 06:44:13 → 06:44:28 | complete rc 0 (receipt `recorded_epoch` 06:44:18) | 記録 insight §3、receipt.json |
| 06:45:00 → 06:45:38 | materialize rc 0 (公開 leaf 4 file) | 記録 insight §3 (mtime) |

- 再投入は行われていない (認可は 1 attempt。落ちていないので再走の要否は生じていない。事前登録 §6.4 は性能値を再投入理由にしない)。
- `bench_wall_s` (約 100 秒 / arm) と job elapsed の差は、build・verify・settle・probe・barrier 待ちと campaign の外側の処理である。
  本稿はその内訳を分解しない。

### 2.6 図 — `figures/fig9_a1_balanced5_sized_attempt1.{png,pdf,provenance.json}`

- 生成器 `tools/plotting/plot_a1_sized_paired.py` (規約 `tools/plotting/FIGURE_CONVENTIONS.md`)。1 行 × 3 列 (write-heavy /
  balanced / read-heavy)、各 panel に 30 対の差 (variant − baseline、pair index 順)、対差平均の実線と平均 ± h の帯、
  0 の実線、±B の破線。y は workload ごとの尺度で、panel 間で高さを比べない。
- **図の値の出所は §2.1 と同じ `result.json` の `statistics` と `pairs`** である。生成器は 30 対から mean / s / h / B を
  再計算して `statistics` と fail-closed で照合し、分類は記録値を写して述語で検算する。provenance JSON の `workloads[]`
  (cells) と `artist_series` が「描いた値」の機械可読な正本で、`orchestrator/tests/test_plot_a1_sized_paired.py` が
  (a) fixture 上で表示値 = cells = 再計算値、(b) 着地した図の PNG / PDF の sha256・caption・cells が provenance と現行 leaf に
  一致すること、(c) 生成器の pin 表が本稿 §5.1 の sha256 と一致することを検査する。
- **本稿は図の provenance JSON の sha256 を書かない。** 図の provenance は本稿を `caption_source` として sha256 で束縛する
  (限定と条件の言い方の出所。数値・分類の出所ではない) ので、本稿が provenance の sha256 を持つと相互参照になる (F36)。
  provenance JSON の sha256、キャプション正文、proof chain の正本は `docs/paper-story/figures/README.md` の fig9 節が持つ
  (fig8 と同じ形)。結果節の表の数値は本稿 (= result.json) から、図は figures/ から取り、両者の同一性は上の test に委ねる。
- caption は英文で、lane の 3 値 (`formal: false; promotion_prohibited: true; result_authority: sized-preregistered-descriptive-only`)、
  「単一 attempt・headline 値でない・workload 横断の結論を作らない・C1 の再現ではない・反復間の安定性を言わない」の固定文、
  測定条件、正しさは別走行で性能認証ではないこと、panel 間で y を比べない注意を含む。図番号は出力 prefix `fig9_` から導く。

---

## 3. 限定 (この結果が言わないこと)

| # | 限定 | 出所 |
|---|---|---|
| L-A1S-1 | **非認証 lane の結果である。** `formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only` は結果を見た後も動いていない。これらは事前登録と policy の編集だけで反転させない | policy `authority`、事前登録 §1.1 / §7.2 |
| L-A1S-2 | **headline 値にしない。** 論文の主張の数値 (C1 等) にこの attempt の値を置かない。「A-1 の値がある」と書けるかどうかは本稿の外の裁定である | D2044 項 8、stale 注記 3 件目 |
| L-A1S-3 | **workload をまたぐ結論を作らない。** 3 行の表は並記であり、「2 勝 1 敗」「平均して改善」のような集計・要約を作らない | 事前登録 §7.2、result.json `limitations` 4 項目め |
| L-A1S-4 | **単一 attempt を反復間の安定性へ一般化しない。** attempt-0001 が 1 本あるだけで、attempt 間の再現性は測っていない。同じ study の pilot は反復数の決定にだけ使われ、比較対象でも再現例でもない | 事前登録 §7.2、policy `sizing_inputs` |
| L-A1S-5 | **C1 の再現判定にしない。** 符号が C1 の旧環境値と 3 workload とも一致することは観察であって再現ではない。推定対象 (対差の算術平均 対 比)、環境 (Pegasus 計算ノード 対 D496 以前の環境)、分母の処理が異なる | D1993、claim-evidence `L23`、D1262 |
| L-A1S-6 | **推定対象は 5-rep 均衡スケジュール下の差であり、残留効果の無い定常状態の直接効果ではない。** 対の中の 2 測定の間隔は有限で、順序・時間隔の交絡を消したという主張ではない | 事前登録 §3、`limitations` 1 項目め |
| L-A1S-7 | **区間と分類は descriptive な出力である。** `h = k·s/√n` の k は事前登録が arm 失敗確率の目標 1/120 から固定した t 分位点で、本稿はこれを「有意差」「p 値」「検出力」の言葉へ翻訳しない。`resolved-above-floor` は「区間が床の外」という札であって効果の存在証明ではない | 事前登録 §5.1 / §5.2 |
| L-A1S-8 | **床 B は baseline 平均の 3% という相対量で、この attempt の baseline 平均から計算されている。** 他の走行・他の環境の絶対値の床ではない (`past_run_absolute_tps_prohibited`) | policy v2 契約の文言 (v3 実装は定数 0.03)、`statistics.floor_fraction` |
| L-A1S-9 | **性能の判定と正しさの証拠は別の段である。** §2.4 の `certified` は `legacy` 検査条件の下の直列化可能性までを言い、性能認証ではない。逆に、性能の出力がどうであれ正しさ証拠の有無は変わらない | 絶対規律 1・2、D1993 項 2 |
| L-A1S-10 | **`legacy` 検査条件の実引数は本 attempt の成果物に無い。** WAL は `workload.tag = legacy` とだけ記録し、tuple 数・thread 数・rratio・rmw・extime は別の一次資料 (束縛 code) からしか導けない。本稿はそれを導いていない | §4.1 |
| L-A1S-11 | **source binding は artifact 単独の証明ではない。** `evidence_level = source-routed-trace0`、`artifact_standalone_proof = false`。build が束縛 file の bytes から行われたことは成果物の外の経路 (job preflight・submit 時の HEAD 検査) に依る | result.json `source_binding`、`limitations` 3 項目め |
| L-A1S-12 | **scheduler の終了状態は未観測である。** 3 job とも終端後に `qstat` から消えた形で、exit_status / state は記録されていない。成功は driver rc / shell rc / status で確定している | result.json `materialization_evidence`、completion 受領証 |
| L-A1S-13 | **公開 leaf の publish は非協力的な書き手に対して原子的な no-replace ではない** (`RENAME_NOREPLACE` が EINVAL、fallback の限界)。本 attempt では衝突は起きていない | `.complete.json` `publish.limitations`、`limitations` 5 項目め |
| L-A1S-14 | **abort 率・latency・cache・IPC は測っていない。** leading indicator は throughput だけで、機序 (なぜ read-heavy で負か) は本 attempt から言えない | WAL `bench_done.leading_indicators` |
| L-A1S-15 | **他の attempt・他の series とプールしない。** A-2 (`t2364-20260907b`)、A-6 (`a6-20260908b`)、[T-1998] の balanced 対は別の protocol・別の推定量 (median 比) で、本 attempt と足し合わせない。B-7 の要件充足でもない | D1993 項 6、D2044 項 3 |
| L-A1S-16 | **他の CCBench pin・他の機体・他の read 比率への転移は言わない。** 測ったのは pin `511c9538`、Pegasus `gen_S` の bnode107〜109、rratio 5 / 50 / 95 だけである | policy `ccbench_acceptance`、receipt `reservation_binding` |
| L-A1S-17 | **2 本目の論文 (`docs/paper-story-backoff/`) と数値・図を共用しない** | D1637 |
| L-A1S-18 | **図は記述図である。** fig9 は §2.1 の値を描いたもので、採用判断・性能認証・主張の根拠にしない (絶対規律 2)。panel 間で y を比べない | §2.6、FIGURE_CONVENTIONS |
| L-A1S-19 | **baseline の cv が variant より大きいこと (§2.3) の理由を述べない。** 観察であり、機序・環境要因の帰属はしていない | §2.3 |
| L-A1S-20 | **1 attempt の所要 (投入から materialize まで 15 分) は再投入の予算や計画値ではない。** 所要は job の accounting と WAL の ts から書いた事実で、別の attempt がこの時間で終わるとは言わない | §1.4、§2.5 |

---

## 4. 欠落 — 権威 bytes・WAL・事前登録・裁定の対応が確かめられない箇所

### 4.1 成果物に情報が無い

- `legacy` 検査条件の実引数 (§3 L-A1S-10)。
- verify の trace-enabled build の識別子 (`trace_bin_sha256`) は WAL `build_done` にあるが、本稿は 6 本の値を転記していない
  (正しさ証拠の同一性は `verify_done_frames` の `raw_sha256` が WAL 行を束縛する形で result.json が持つ)。
- perf は使っていないので、cache miss 率・IPC は存在しない (欠落ではなく設計)。

### 4.2 束縛の範囲が限られる

- 公開 leaf の `result.json` (`372f199e…`) は raw の `raw/results/result.json` (`b080d755…`) と bytes が異なる。差は materializer が
  足した `materialization_evidence` と `limitations` 5 項目め (publish fallback) だけで、`workloads[].statistics` と `arms` は
  構造比較で同一である (本稿の作成時に照合)。receipt.json の `result.sha256` と `materialization.raw_result.sha256` は raw を指す。
  **本稿の数値は公開 leaf から取り、raw との同一性は本稿の作成時の照合に依る。**
- source binding の 9 file は `git_blob_oid` と `working_sha256` で束縛されるが、投入 worktree が detached であることと
  tracked-clean の検査は成果物の外 (job preflight、記録 insight §2.1) に記録がある。

### 4.3 本稿で対応を再確認していない

- `balanced-schedule-receipt.json` (3 本、sha256 は result.json `schedule_receipt` と一致することを照合した) の中身 —
  seed からの bit 導出と物理順の再現は本稿では行っていない。policy の `pairing.seed` 規則と `invalid_rules`
  (「schedule receipt が凍結 seed 導出と物理順から異なる」) が producer 側で検査した、という記録に依る。
- campaign.lock の `identity_preimage` 全文 (loader 束縛の blob 一覧) と `build_admission` の中身 — arm order と genome だけを照合した。
- job stdout / stderr (記録 insight の `receipts/job-std*.txt`) の全文 — verify の 1 行だけを §2.4 の照合に使った。

---

## 5. 一次資料

### 5.1 権威 bytes と転記元 (repo 内、tracked) — `output/insights/2026-09-13/paper-story-a1-balanced5-sized/`

本稿の作成時 (2026-09-18) に現物 bytes から再計算した SHA-256。生成器 `tools/plotting/plot_a1_sized_paired.py` の pin 表は
この表と同じ値を持ち、`orchestrator/tests/test_plot_a1_sized_paired.py` が両者の一致を検査する。

| file | SHA-256 | bytes |
|---|---|---:|
| `output/insights/2026-09-13/paper-story-a1-balanced5-sized/result.json` | `372f199e674cce28d46e2aeeed90b0f5b6c06e894bca63bcb779b580a8bb75a0` | 269649 |
| `output/insights/2026-09-13/paper-story-a1-balanced5-sized/receipt.json` | `a2039dc1457cf34828714a98955faf3df68d335c0442d144122686f4e177e930` | 19343 |
| `output/insights/2026-09-13/paper-story-a1-balanced5-sized/.complete.json` | `0b1f177944f6cab5c5eed5aa94a34beda11a06fcd8e94c1018d35c4e5e212a1e` | 1392 |
| `orchestrator/campaign/paper_story_a1_paired.v3-sized.json` | `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a` | (policy。result.json `policy_sha256` と一致) |

- `.complete.json` の `files` map: README.md `880919db73901d44ed3f8e6508239267d1acc15c2be997603edbe2b7c6db2d88`、
  receipt.json `a2039dc1…`、result.json `372f199e…` (上と一致)。schema `paper-story-a1-paired-materialization-complete/v1`、
  publish 機構 `a1-exclusive-claim-check-then-renameat2`。
- 公開 leaf の `README.md` (materializer の出力) は §2.1 の表を 6 桁固定小数で持つ (`1591948.500000` 等)。本稿は
  result.json の float を逐語で写した (`README.md` を出所にしていない)。
- 最上位 `authority` は schema v3 の固定値 `exploratory` (materializer の契約) で、policy の `result_authority`
  (`sized-preregistered-descriptive-only`) とは別欄である。

### 5.2 durable authority (repo 外) — `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/`

本稿の作成時に現物から再計算し、result.json の記録値 (sha256 と bytes) と一致することを確認した。

| workload | file | SHA-256 | bytes |
|---|---|---|---:|
| write-heavy | `jobs/write-heavy/raw/campaign-output/exploration/campaigns/paper-story-a1-write-heavy-paired-ec74e1c8/campaign.lock` | `3d3b094e5082147eb83a03ece85067b608beba07a52c965562dbb323f77c2bf6` | 5463 |
| write-heavy | 同 `…/runs/wal.jsonl` | `43b02eef2a1c16978f6351e591864f4a4d72601f42f76dfa71a6bb469051cd4f` | 17933 |
| write-heavy | 同 `…/balanced-schedule-receipt.json` | `137b0cc6d263d51db5196f3367f1d77b19e3ec66b6a3d590b8329c55d3cfa28d` | 12942 |
| balanced | `jobs/balanced/raw/campaign-output/exploration/campaigns/paper-story-a1-balanced-paired-fdd1cb88/campaign.lock` | `3fb0688713962867c6fcd5005b77e81317b61424bf91d718f7b552c5e10f9c1a` | 5433 |
| balanced | 同 `…/runs/wal.jsonl` | `e2530dfec7ed43b30bda282cf1a2d41527f9c68363a90c4aed39fbfafa824511` | 17863 |
| balanced | 同 `…/balanced-schedule-receipt.json` | `2ebe5c4f59a42817e4eb41ee3136d87c540b120c0739257d35d69dbb5b326a2b` | 12895 |
| read-heavy | `jobs/read-heavy/raw/campaign-output/exploration/campaigns/paper-story-a1-read-heavy-paired-9912d892/campaign.lock` | `32a213246ed2d8b542df43a82323aa890147caea4fd37deb187bd0515dcf6775` | 5447 |
| read-heavy | 同 `…/runs/wal.jsonl` | `4001e27c10008eeb98a45ffa8295d209cc3595cd7c5f6e68ed93f6fde2dbb87c` | 17940 |
| read-heavy | 同 `…/balanced-schedule-receipt.json` | `9b2541ae294cd15afb73b40021b169a69f2a909dacf6cd2b480b58f3c0d2518a` | 13005 |

- raw results: `raw/results/result.json` `b080d755f5c6e3df1961d7355fffce923d23827547c9f711eaf7c2986450ace2` (263360 bytes)、
  `raw/results/receipt.json` `7de00bf5515d56a2e6fc791acaa0f505476db60ec7ecacab3dbc15d8ed6b32cb` (18112 bytes)
  (§4.2 のとおり公開 leaf とは bytes が違う)。
- 受領証: `receipts/submission.json` `0a86dec922ff0a77bc2798cda466c646e2d29fdb4cf84c013a933ae271f3ddb4`、
  `receipts/completion.json` `d26c4852150ba5e76f528790aa7e39e3ea155f6d2c43619dd561fcb55193d98f`、
  `raw/job-terminal.json` `c46ae55cd9be5866956d5ffdefe5b86326de5899e8aa611725d6cf51631bbd15`、intent
  `attempt-0001.intent.json` `0c3aadaea83f0fe1c7a31777d26bf992fbd46d64f6e1ed12a2de2cc6f67923d2`
  (いずれも記録 insight の `MANIFEST.tsv` と `receipts/` に複製と sha256 がある)。
- campaign id: `paper-story-a1-write-heavy-paired-ec74e1c8` / `paper-story-a1-balanced-paired-fdd1cb88` /
  `paper-story-a1-read-heavy-paired-9912d892` (`recomputed_campaign_id` と一致)。WAL の `env_tag` は 3 本とも `pegasus`、
  `line_issues = []`、`truncated_tail = false`。

### 5.3 repo 内 (tracked) の一次資料

- 事前登録 `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md` (§1.1 の sha256)。
- policy `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`、実装 `orchestrator/campaign/paper_story_a1_paired.py`
  (`_classify_difference`、`_statistics_from_signed_differences`)、source 契約 `orchestrator/campaign/paper_story_a1_source.v2.json`、
  追補 `output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md`、patch `patches/silo-backoff-fixed.patch`、
  job body `tools/pegasus/paper_story_a1_paired.sh` (いずれも result.json `source_binding.files` の 9 本に含まれる。
  measurement source commit `d2ebef7a407dc6be61622ed596cf08b8b518f606`)。
- 記録 insight `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md` (投入・時系列・受領証。§2.4 に記した表の差を
  除き本稿の記述と一致。本稿は同 insight を数値の出所にしていない)。
- 本稿を書いた wave の insight `output/insights/2026-09-18/t2775-a1-sized-results-draft/README.md` (検算の逐語、レビュー)。

### 5.4 裁定

- D2120 項 3 (2026-09-17、1 attempt の認可)、D2044 項 8 / D1986 項 5 (認可の据え置きとユーザー手番)、D1262 (estimand の揃え直し)、
  D1631 (results 系列の規則)、D1858 (stale 注記)、D1993 (再現判定の区別、項 6 のプール禁止)、D1637 (2 本目の論文と共用しない)、
  D12 (protocol status を成否の宣告へ拡張しない)、D2120 項 15 (単独 results 稿の型 = [T-2611] / [T-2674])。

### 5.5 値の出所 (転記した数値ごと)

| 数値 | 出所 |
|---|---|
| §2.1 の mean / h / 区間 / B / baseline mean / sd / planned sigma / k / df / 分類 / breach | result.json `workloads[].statistics` (逐語) |
| §2.2 の 180 標本と 90 対差 | result.json `workloads[].statistics.pairs` |
| §2.3 の mean / min / max | result.json `arms.<name>.raw_tps` から本稿が計算 (派生値) |
| §2.3 の median / cv、§2.4 の commits / aborts / anomalies / verdict、§2.5 の WAL 時刻 | 各 workload の `runs/wal.jsonl` (`bench_done` / `verify_done` / `ts`) |
| §1.4 の request / host / elapsed / CPU / 時刻 | receipt.json `job_executions` (`accounting`、`reservation_binding`) |
| §1.4 の submit / complete / materialize の時刻 | 記録 insight §3 (job dir file の mtime。本稿はこの時刻を再計測していない) |
| §1.1〜§1.3 の条件 | policy v3-sized.json、事前登録 README、WAL `build_start.genome` / `bench_done.run_cmd` |
| §5.1 / §5.2 の sha256 と bytes | 本稿の作成時に現物から再計算 |

### 5.6 同じ結果についての既存の記述 (本稿の出所ではない)

- `docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」3 件目 (2026-09-18、[T-2775]) — attempt の完走を
  指す stale 注記。本稿はそこから数値を取っていない。
- `docs/paper-story/2026-09-17.md` §8 の A-1 項 — 執筆時点 (本走未投入) の記述で、凍結物として残る。
- `docs/paper-story/claim-evidence/2026-08-26.md` の A-1 行と `L23` — 旧 policy v2 (`static10 − adaptive`) 前提の凍結物で、
  D1262 以後の study と本 attempt を反映していない。

---
