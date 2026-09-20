# A-1 balanced5 sized 本走 attempt-0002 (認可済み独立再現) の結果節 — 3 workload の登録済み解析は `resolved-above-floor` (符号 +/+/−)、`variance_plan_breach` は write-heavy / read-heavy で true、非認証 lane の descriptive 出力と attempt-0001 稿の並記 (2026-09-20)

**これは投稿本文ではない。** 論文の結果節・表・図・限定へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の既存の稿を改めるものではない。** attempt-0001 の稿 `results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`
(以下「attempt-0001 稿」) は凍結物として残り、本稿はそれを改訂しない。本稿は **attempt-0002 の単独稿**であり、§2.7 に attempt-0001 稿の値を
**並記**するが、2 attempt の値をプールした推定量・差・比・合成区間は作らない (D1993 項 6)。**本稿は版 (`2026-09-20.md`)・claim-evidence 稿・
stale 注記・記録 insight の本文を測定値・統計値の出所にしていない。** 出所は §5 に挙げる一次資料 (公開 leaf の result.json / receipt.json、
campaign WAL、schedule receipt、事前登録、policy、追補、認可 record、裁定) だけである。例外は authorize-rerun・submit・complete・materialize の
時刻で、これは本稿を書いた wave の job dir file の mtime に依る (§5.5 に明記)。

**本稿が判定しないこと (最初に置く):** A-1 の充足、`formal=false` から formal への昇格、attempt 間の再現性・反復間の安定性 (attempt-0001 稿の
限定 L-A1S-4 の解除)、3 本目の attempt の認可、のいずれも本稿は判定しない。認可はユーザー手番である (D2044 項 8、D2120 項 3、D2172 項 2)。
本稿は「attempt-0002 が何を出力したか」を一次資料から書き写し、attempt-0001 の出力を隣に置く文書であり、「A-1 の値がある」「再現した」と
書けるかどうかは本稿の外の裁定に属する。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

- **1 attempt = attempt-0002** (study `paper-story-a1-20260901-balanced5-sized-v1`、投入 2026-09-20 18:11 JST、3 job
  `13220.nqsv` / `13221.nqsv` / `13222.nqsv`)。D2172 項 2 (2026-09-20) が「同一配置 (同 seed・同物理順) の反復」を研究目的として 1 attempt
  限定で認可した独立の観測 attempt であり、attempt-0001 の失敗後の再走ではない (追補 §6.4 項 4)。sized の attempt はこれで 2 本 (attempt-0001 は
  2026-09-18)。再投入は行われていない (§2.5)。
- **3 workload × 各 30 対 × 2 arm** = 180 測定。3 workload は同じ study の中の独立した campaign (別 job・別 node) であり、
  **workload をまたぐ結論は作らない** (事前登録 §7.2、result.json `limitations` 4 項目め)。本稿の表が 3 行あるのは並記であって集計ではない。
- 本稿の「登録済み解析」とは、事前登録 (§1.1) と policy v3 が結果を見る前に固定した推定対象・区間・分類規則を、materializer が result.json へ
  書いた出力を指す。attempt-0002 に対する規則は attempt-0001 と同じ file (事前登録・policy) が定め、追補 (§1.4) はこの規則を変えていない。

### 0.2 書くもの

- 権威 bytes (公開 leaf の `result.json`) が持つ 3 workload の `statistics` (対差の算術平均、標本標準偏差、`h`、記述区間、`B`、baseline 平均、
  分類、`variance_plan_breach`) と、それを作った 30 対の生値 (§2.2)。
- 各 arm の 30 標本の記述 (§2.3)、campaign WAL の `verify_done` が記録した正しさの判定 (§2.4)、時系列 (§2.5)。
- 結果を見る前に固定していた条件 (§1)、attempt-0001 との比較可能条件 (§1.5)、attempt-0001 稿の値の並記 (§2.7)、この結果が言わないこと (§3)、
  一次資料 (§5)。

### 0.3 書かないもの

- 研究として成功か失敗かの宣告 (D12)。3 workload の符号 (+ / + / −) を「採用静的 backoff の優劣」へ拡張すること。
- **headline 値としての採用。** この lane は `formal=false` / `promotion_prohibited=true` / `result_authority = sized-preregistered-descriptive-only`
  であり、policy と事前登録がその反転を文書編集で行うことを禁じている (事前登録 §7.2)。追補も lane を変えない (追補「限界」)。
- **attempt-0001 との差・比・プールした推定量・「再現した / しなかった」の判定。** §2.7 の並記は 2 つの観測を横に置くだけであり、
  2 attempt の対差平均の差、区間の重なり、符号の一致を「再現性の判定」として書かない。attempt-0001 稿の限定 L-A1S-4 (単一 attempt を反復間の
  安定性へ一般化しない) の解除可否は、追補が定めるとおり別の裁定に属し、本稿はその材料を提供するだけである。
- **C1 の再現判定。** 符号が C1 の旧環境値 (write-heavy +38.3% / balanced +11.3% / read-heavy −6.6%。照合先は claim-evidence `2026-08-26.md` の
  C1 行、本 attempt の測定値ではない) と 3 workload とも一致することは観察であって再現判定ではない (D1993、claim-evidence の `L23` の区別を維持)。
- **`variance_plan_breach = true` の解釈。** write-heavy と read-heavy で標本 sd が事前登録の計画 sigma を超えたことは記録値として書くが、
  その原因の帰属 (node・時間帯・bench 順・baseline arm の変動) は本稿では行わない (§3 L-A1S2-8)。
- A-2 / A-6 / [T-1998] との集計 (D1993 項 6)、pilot の観測値の混入 (事前登録 §7.2)、機序の同定、他の CCBench pin・他の機体への転移、
  3 本目の attempt の要否・認可。

### 0.4 主判定文 (結果節へ落とすときの形。文を分けたまま使う)

attempt-0002 (D2172 項 2 が 1 attempt 限定で認可した、attempt-0001 と同じ policy・同じ root seed・同じ物理順の独立再現) の trace-disabled
性能測定では、登録済み解析の出力は 3 workload とも `resolved-above-floor` だった — 対差平均 (variant − baseline) は write-heavy
+1,538,451.47 tps、balanced +548,138.23 tps、read-heavy −560,565.60 tps で、各 workload の記述区間 (平均 ± h) は床 ±B の外にある。
write-heavy と read-heavy では 30 対の差の標本標準偏差が事前登録の計画 sigma を超え (`variance_plan_breach = true`、比 1.21 / 1.08)、
balanced では超えていない (0.87)。これは事前登録した分類規則の descriptive な出力であり、仮説検定でも性能認証でもない。この lane は
`formal=false` / `promotion_prohibited=true` のままである。attempt-0001 (2026-09-18) の登録済み解析も 3 workload とも `resolved-above-floor`
で符号は同じ (+ / + / −) だが、本稿は 2 attempt をプールせず、再現性の判定も行わない (§2.7)。別の trace-enabled 走行では、6 arm とも
`verify_done` が `certified=true` / `anomalies=0` / `verdict=serializable` と記録されており、それは性能の判定ではない (§2.4)。

---

## 1. 条件 — 結果を見る前に固定したもの

### 1.1 事前登録と policy (attempt-0001 と同じ file・同じ bytes)

- 事前登録: `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md`
  (sha256 `6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2`、policy の `preregistration` field が束縛。attempt-0001 と同じ値)。
- policy: `orchestrator/campaign/paper_story_a1_paired.v3-sized.json` (`paper-story-a1-paired-policy/v3`、
  sha256 `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a`。result.json の `policy_sha256` と receipt.json の `policy.sha256` が
  同じ値を持つ。attempt-0001 と同じ値)。
- `authority`: `formal=false`、`promotion_prohibited=true`、`result_authority="sized-preregistered-descriptive-only"`。
- 推定対象 (`pairing.estimand`): `arithmetic mean of paired differences under the balanced five-rep schedule`。contrast は
  `variant-minus-baseline`、配置は `balanced-a5b5-b5a5-v1` (10 対を 1 群とし、群ごとに seed から引いた 1 bit で `A^5 B^5 B^5 A^5` か
  `B^5 A^5 A^5 B^5` の物理順を決める。A = variant、B = baseline)。
- 反復数: 3 workload とも `reps=30` (`df=29`)。`k = 2.8315526875186725` (`t(1 − (1/120)/2, 29)`、事前登録 §5.1)。
  `planned_sigma_tps` は write-heavy `66403.452108019716`、balanced `56697.435713574683`、read-heavy `74668.489566274948`
  (policy の文字列値。result.json は float 化した値を持つ)。
- 区間と床 (事前登録 §5.1): `h = k · s / √n` (`s` = 30 対の差の標本標準偏差)、区間 `[mean − h, mean + h]`、`B = (3/100) × (その workload の
  baseline 平均)`。
- 分類 (事前登録 §5.2 と実装): `abs(mean) − h > B` → `resolved-above-floor`、`abs(mean) + h ≤ B` → `bounded-below-floor`、それ以外 → `unresolved`。
  **事前登録 §5.2 の語 (`resolved-beyond-floor (improvement / regression)` / `bounded-within-floor`) と、実装・result.json の語
  (`resolved-above-floor` / `bounded-below-floor`) は異なるが、述語は同値である** (`L > B` または `U < −B` ⟺ `abs(mean) − h > B`)。向きは
  平均の符号で読む。述語は実装 `orchestrator/campaign/paper_story_a1_paired.py` の `_classify_difference` にあり、`floor_fraction` は同 file の
  `_statistics_from_signed_differences` が v3 では定数 0.03 として持つ。
- `variance_plan_breach`: `sample_sd > planned_sigma_tps` (事前登録の計画 sigma を標本 sd が超えたか)。**本 attempt では write-heavy と
  read-heavy が true、balanced が false** (§2.1)。この field は記録値であり、分類 (`resolved-above-floor`) を変える入力ではない
  (分類は `mean` と `h` と `B` だけで決まる)。
- pilot の観測値は反復数の決定にだけ使い、最終推定へは 1 点も入れない (policy `sizing_inputs`、事前登録 §7.2)。

### 1.2 arm と genome (policy `workloads[].arms`、campaign.lock の `identity_preimage`、WAL `build_start.genome` と一致。attempt-0001 と同じ)

| workload | rratio | variant arm (minuend) | baseline arm (subtrahend) |
|---|---:|---|---|
| write-heavy | 5 | `fixed10`: `silo\|BACKOFF_FIXED=10,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` | `no-backoff`: `silo\|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| balanced | 50 | `fixed5`: `silo\|BACKOFF_FIXED=5,BACK_OFF=1,…` (他 3 flag は同じ) | 同上 |
| read-heavy | 95 | `fixed2`: `silo\|BACKOFF_FIXED=2,BACK_OFF=1,…` (他 3 flag は同じ) | 同上 |

variant の識別子 (WAL の `variant`): `fixed10` = `a7f8486e1116`、`fixed5` = `93c62227a2d3`、`fixed2` = `82ea3a7b8618`、
`no-backoff` = `84319b1127a6` (3 workload で共通。attempt-0001 と同じ識別子)。静的 backoff は `patches/silo-backoff-fixed.patch`
(source binding の 1 本、attempt-0001 と同じ bytes) が入れる枝であり、`BACK_OFF=0` の baseline はその枝も CCBench 内蔵の適応 backoff も持たない。

### 1.3 測定条件 (policy `scale` / `execution`、WAL `bench_done.run_cmd`。attempt-0001 と同じ)

- records 1,000,000、threads 48、`ycsb_zipf_skew` 0.9、`ycsb_rmw` 0、`ycsb_max_ope` 10、`extime` 3 s、`clocks_per_us` 2100、
  protocol silo、CCBench pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` (`ccbench_acceptance.canonical_pin`)。
- 実行の形: workload ごとに fresh な exact 2-arm campaign を 1 つ、両 arm の build と verify が終わってから bench、bench は 1 round
  (`bench_max_rounds` 1)、5-rep block ごとに競合テナント probe (fail-closed)、settle は workload schedule の開始時に 1 回、`site` は
  `pegasus-compute-only`、自動再試行なし。bench lock は workload ごとに 1 回獲得 (`bench_lock_acquisitions_per_workload` 1、
  `bench_lock_scope` = 両 arm の build + verify 後の全 5-rep block)。
- source: `measurement_source_commit = fec4a818741e5464fffcd11e4b094c125dfe5280` (着手直前の local main、投入 worktree は detached)。
  attempt-0001 の `d2ebef7a407dc6be61622ed596cf08b8b518f606` とは**異なる commit** である (差の中身は §1.5)。`source_binding.evidence_level =
  source-routed-trace0`、`artifact_standalone_proof = false` (成果物単独では build 経路を証明しない。束縛 file 9 本の blob oid と working sha256 は
  result.json `source_binding.files`)。
- perf は使っていない (`bench_done.perf_observation.use_perf = false`、`counter_status = not_required`)。leading indicator は throughput だけで、
  abort 率・latency・LLC・IPC は null。
- 正しさの検査条件 (`legacy`) は WAL の `verify_done.workload.tag` に `legacy` とだけ記録されており、その実引数は本 attempt の成果物には無い (§4.1)。

### 1.4 認可 record・追補・投入・受領証

- 裁定: D2172 項 2 (2026-09-20) が「同一配置 (同 seed・同物理順) の反復」を研究目的と確定し、択 1 (exact な認可 record を gate の入力に取る) を
  attempt-0002 の 1 attempt 限定で認可した。実装は D2178 (commit `886c19259`、driver の rear gate `_assert_no_prior_v3_bench_start` と公開先 gate
  `_exact_materialization_destination` に exact な record の入力を足し、producer `authorize-rerun` を追加)。
- 追補: `output/insights/2026-09-20/t2792-a1-sized-preregistration-amendment/README.md` (commit `ec696308a`、sha256
  `0098d4ea5a7d71abc3c4a269f418ce9d29bf394fb242d1a5d6ace6652614311d`、`authority: preregistration-amendment`)。事前登録 §6.1 / §6.4 に対する
  「将来の attempt-0002 一件」だけへの別版であり、元の事前登録・policy・source 契約 v2・source 追補の bytes を保存し、attempt-0001 の判定・
  公開 leaf・稿・図・限定 L-A1S-4 を遡及変更しない。**追補は erratum ではない。** 追補 file 自身の実行時 digest 検査は無く、束縛は source
  commit 経由 (record の `source_commit` = `submit` / `materialize` の `--expected-head`)。
- 認可 record: durable base 直下 `attempt-0002.authorization.json` (file sha256 `8204f9759e51fc2b357fbad5d7edaf5464974fc1cee2e4862749d4598c43d685`、
  501 bytes、2026-09-20 18:10:34 JST に `authorize-rerun` が create-only で書いた)。内容 = `schema_version`
  `paper-story-a1-paired-rerun-authorization/v1`、`study_id` (sized)、`attempt_root` (base 直下 `attempt-0002`)、`source_commit`
  `fec4a818741e5464fffcd11e4b094c125dfe5280`、`decision` `{id: D2172, item: 2, decided_on: 2026-09-20}`、`authorization_sha256`
  `9ccd38c995d225d151e4572c7f878f908f46ff90f0a95b886cc20819e152e40c` (`authorization_sha256` 自身を除いた record の canonical JSON の digest。破損検出用であり署名ではない)。
  driver 側の定数 `V3_SIZED_RERUN_AUTHORIZATIONS` = (sized study, `attempt-0002`, `attempt-0001`, `D2172`, 2, `2026-09-20`) と exact 一致するときに
  限り、rear gate は先行 attempt-0001 の bench 到達に対する group 再投入禁止だけを解除し、公開先 gate は兄弟 dir を受理する。
- submit: `paper_story_a1_paired submit --study-id paper-story-a1-20260901-balanced5-sized-v1 --expected-head fec4a8187…` (2026-09-20 18:11:15 →
  18:11:16 JST、rc 0)。route `direct-qsub-workload-fanout`、submission 受領証が持つ intent の canonical digest (`intent_sha256`)
  `6bc38262ad4d309154808c234ad601394e4872c2e87f224c91b684c868c897ea` (intent file 全体の bytes の SHA-256 は §5.2 の `5a66484d…` で、別の値である)。
- job (receipt.json `job_executions` / `reservation_binding`): 3 本とも queue `gen_S`、`requested_s` 21600、job script sha256
  `3c2b734d9c71caca583baa4fd950bb55957dc64e90b2c27ec8e60eb8705fed80` (= `tools/pegasus/paper_story_a1_paired.sh`、attempt-0001 と同じ bytes)。

| workload | request | host | scheduler start (JST) | job end (JST) | elapsed s | CPU total s |
|---|---|---|---|---|---:|---:|
| write-heavy | `13220.nqsv` | bnode035 | 18:11:23 | 18:28:53 | 1050.02 | 9080.502 |
| balanced | `13221.nqsv` | bnode039 | 18:16:47 | 18:22:08 | 321.32 | 9081.926 |
| read-heavy | `13222.nqsv` | bnode040 | 18:11:23 | 18:25:31 | 847.45 | 9108.688 |

(時刻は `accounting.started_epoch_s` / `ended_epoch_s` を JST へ換算。CPU は job body の Bash `times` の差分。attempt-0001 の node は
bnode107 / 108 / 109 で、本 attempt とは別 node である。)
- balanced (`13221.nqsv`) は request 作成 (NQSV accounting 18:11:15、`Pre-running` への遷移 18:11:16) から scheduler start (18:16:47) まで
  記録上 5 分 31 秒を要した (本稿を書いた wave の観測: 投入直後の `qstat -f` は Current State = Pre-running、Execution Hosts = bnode039、監視 log は
  18:12:11〜18:16:12 に PRR、18:17:12 に RUN)。他 2 job は request 作成 18:11:15 (write-heavy) / 18:11:16 (read-heavy) で scheduler start はともに 18:11:23。
- scheduler terminal: 3 本とも `request-disappeared-after-visibility` (投入時に `QUE` で可視、終端後の `qstat` が `does not exist` を返す形)。
  state / exit_status は「未観測」と記録され、成功は `driver_rc=0` / `shell_rc=0` / `status=finished` で独立に確定している
  (result.json `materialization_evidence.interpretation`、completion 受領証 `jobs[].scheduler_terminal`)。
- complete: 18:30:05 → 18:30:06 JST (rc 0、receipt `recorded_epoch` 18:30:05、completion 受領証 sha256 `11202bf7…`、group terminal sha256
  `a9bc5f9a150533fd3900140bd2dea1b307c9706e2862158a3a98499a6af6cb38`)。materialize: 18:30:21 JST (rc 0、公開先 = 兄弟 dir
  `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002`、公開先 gate が record 一致で受理)。

### 1.5 attempt-0001 との比較可能条件 (結果を見る前に固定していたもの。同じ測定値が出ることを意味しない)

| 項目 | attempt-0001 (2026-09-18) | attempt-0002 (本稿) | 出所 |
|---|---|---|---|
| study / policy / 事前登録 / source 契約 v2 / source 追補 / patch / job body | sha `a6228bcd…` / `6047eff0…` / `b50a4edf…` / `6093de24…` / `a5e0710c…` / `3c2b734d…` | 同値 (bytes 同一) | result.json `source_binding.files` の `working_sha256` (2 attempt で一致)、policy の `preregistration` |
| 束縛 9 file のうち driver 以外 8 本 (`runner.py` / `v3-sized.json` / `a1_source.py` / `source.v2.json` / `pipeline.py` / source 追補 / patch / job script) | blob oid・working sha | 同値 | 同上 |
| driver `orchestrator/campaign/paper_story_a1_paired.py` | working sha `62c10187…` (blob `8af3ff86…`) | working sha `9e69bae4…` (blob `47c94e1d…`)。**異なる** | 同上 |
| source commit | `d2ebef7a407dc6be61622ed596cf08b8b518f606` | `fec4a818741e5464fffcd11e4b094c125dfe5280`。**異なる** | `measurement_source_commit` |
| root seed / effective root seed / seed_counter / group_bits (物理順) | write-heavy `e82d0c26…` / 同 / 0 / `[1, 0, 0]`、balanced `f322d1da…` / 同 / 0 / `[1, 1, 0]`、read-heavy `9ad57bf7…` / `bd459634…` / 1 / `[1, 0, 1]` | **同値** (3 workload とも 4 field が一致、block の arm 順 12 個も一致) | schedule receipt `document` (`root_seed` / `effective_root_seed` / `seed_counter` / `group_bits` / `blocks[].arm`) |
| campaign id (`recomputed_campaign_id`) | `…-write-heavy-paired-ec74e1c8` / `…-balanced-paired-fdd1cb88` / `…-read-heavy-paired-9912d892` | 同値 | result.json `campaign_id` |
| campaign.lock の `identity_preimage` | — | `common_record` の `intent_sha256` / `source_binding_sha256` / `source_commit` と `identity_tag` の 4 箇所だけが異なり、arm・genome・scale・環境契約は同じ | campaign.lock (`canonical_preimage`) の 2 attempt 比較 |
| CCBench pin / third-party 5 source | `511c9538`、masstree `b3c5d054` / mimalloc `02a2f5df` / googletest `f8d7d77c` / gflags `e171aa2d` / glog `8f9ccfe7` | 同値 (hydrate 2 箇所とも pin 一致) | policy `ccbench_acceptance`、hydrate receipt (job dir) |
| node | bnode107 / 108 / 109 | bnode035 / 039 / 040 | receipt `reservation_binding.host` |
| 投入時刻帯 | 06:30 JST | 18:11 JST | receipt `accounting` |

- **driver の差** (`git diff d2ebef7a4 fec4a8187 -- orchestrator/campaign/paper_story_a1_paired.py` = 1 commit `886c19259`、+143 / −3)。変更行の所属 (新版の AST で帰属): module 定数 (`V3_SIZED_RERUN_AUTHORIZATIONS` 等) 15 行、新設した `_exact_v3_rerun_authorization` (51 行) / `_rerun_authorization_digest` (4 行) / `run_authorize_rerun` (41 行)、既存の `_assert_no_prior_v3_bench_start` (8 行) / `_run_submit_v3` (1 行) / `_exact_materialization_destination` (15 行) / `_run_materialize_v3` (2 行) / `_parser` (4 行) / `main` (2 行)。合計 143 行。
  推定量・分類 (`_statistics_from_signed_differences` / `_classify_difference`)・測定 (`run_measurement` と campaign loop) の関数には変更行が無い。
  **これは変更行の所属関数から静的に言えることであり、実行時に等価性を検証したものではない** (§4.3)。
- 「同じ測定条件・同じ解析規則・同じ物理順」と「同じ測定値が出る」は別であり、後者は本表から言えない。

---

## 2. 結果

### 2.1 登録済み解析の出力 (公開 leaf `result.json` の `workloads[].statistics` から逐語。descriptive のみ)

| workload | contrast | n | mean (variant − baseline) tps | h tps | descriptive interval tps | B tps | baseline mean tps | sample sd tps | planned sigma tps | classification | variance_plan_breach |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|---|
| write-heavy | `fixed10` − `no-backoff` | 30 | `1538451.4666666666` | `41434.211082207854` | `[1497017.2555844588, 1579885.6777488743]` | `72952.12299999999` | `2431737.433333333` | `80148.43644687126` | `66403.45210801972` | `resolved-above-floor` | `true` |
| balanced | `fixed5` − `no-backoff` | 30 | `548138.2333333333` | `25552.384438113106` | `[522585.8488952202, 573690.6177714464]` | `110832.746` | `3694424.8666666667` | `49427.359824489315` | `56697.43571357468` | `resolved-above-floor` | `false` |
| read-heavy | `fixed2` − `no-backoff` | 30 | `-560565.6` | `41746.744315864176` | `[-602312.3443158641, -518818.8556841358]` | `305064.861` | `10168828.7` | `80752.98639149407` | `74668.48956627495` | `resolved-above-floor` | `true` |

- `k = 2.8315526875186725`、`df = 29`、`floor_fraction = 0.03`、`pairing_design = balanced-a5b5-b5a5-v1`、
  `contrast = variant-minus-baseline` は 3 workload とも同じ (同 `statistics`)。
- `terminal_result` は 3 workload とも `{status: valid, classification: resolved-above-floor}`、`valid=true`、`errors=[]`。
  最上位は `complete=true`、`all_workloads_terminal=true`、`measurement_error=null`、`formal=false`、`promotion_prohibited=true`、
  `workload_reps` 30 / 30 / 30。
- **符号:** write-heavy 正、balanced 正、read-heavy 負。分類はいずれも「区間が床の外」を言うだけで、向きを持たない。
- **`variance_plan_breach`:** write-heavy `true` (標本 sd 80,148.44 > 計画 sigma 66,403.45)、read-heavy `true` (80,752.99 > 74,668.49)、
  balanced `false` (49,427.36 < 56,697.44)。標本 sd / 計画 sigma の比は 1.207 / 0.872 / 1.081 (本稿の派生値)。事前登録 §5 の反復数 30 は計画 sigma
  を前提に選ばれた値であり、標本 sd がそれを超えた workload では `h` が計画時の想定より広い。それでも `abs(mean) − h > B` が成り立つので分類は
  `resolved-above-floor` である。**本稿はこの超過の原因を帰属しない** (§3 L-A1S2-8)。
- **本稿の作成時に 30 対の生値から再計算した検算:** 3 workload とも `signed_difference_tps = <variant>_tps − no-backoff_tps` が全 30 対で完全一致、
  `pairs[i].<arm>_tps` が `arms.<arm>.raw_tps[i]` と一致、mean / `h` / `B` / 区間 / 分類が上の表と一致 (`s` は最終桁の浮動小数点丸めの範囲で
  一致: read-heavy は `80752.98639149408` を再計算値として得た。他 2 本は記録値と同一表記)。全 180 標本は整数値である。
- **派生値 (登録量ではない。読み手の目安であり、結果節の数値にはしない):** 対差平均 / baseline 平均 = write-heavy +0.633、balanced +0.148、
  read-heavy −0.055。この比の分母は baseline arm の 30 標本の算術平均で、A-2 / A-6 の `adopted_median / stock_median − 1` とも、[T-1998] の
  median 比とも定義が違う。

### 2.2 30 対の生値 (`statistics.pairs`。単位 tps。pair_index の順 = 物理順ではなく対の番号)

write-heavy (`fixed10_tps`, `no-backoff_tps`, `signed_difference_tps`):

| # | fixed10 | no-backoff | diff | # | fixed10 | no-backoff | diff | # | fixed10 | no-backoff | diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 3995893 | 2730303 | 1265590 | 10 | 4003998 | 2419332 | 1584666 | 20 | 3911864 | 2460634 | 1451230 |
| 1 | 3974394 | 2522961 | 1451433 | 11 | 3940048 | 2473584 | 1466464 | 21 | 3960681 | 2390900 | 1569781 |
| 2 | 4006410 | 2487814 | 1518596 | 12 | 3971369 | 2367937 | 1603432 | 22 | 3949564 | 2326624 | 1622940 |
| 3 | 3994803 | 2506498 | 1488305 | 13 | 3963727 | 2351978 | 1611749 | 23 | 3976064 | 2366401 | 1609663 |
| 4 | 3973721 | 2463883 | 1509838 | 14 | 3972163 | 2371776 | 1600387 | 24 | 3963872 | 2388189 | 1575683 |
| 5 | 3977639 | 2465694 | 1511945 | 15 | 3968288 | 2371244 | 1597044 | 25 | 3907069 | 2472573 | 1434496 |
| 6 | 3956407 | 2513015 | 1443392 | 16 | 3988924 | 2338593 | 1650331 | 26 | 3969820 | 2385373 | 1584447 |
| 7 | 4011881 | 2348734 | 1663147 | 17 | 3987553 | 2434821 | 1552732 | 27 | 3977494 | 2462272 | 1515222 |
| 8 | 3968043 | 2389408 | 1578635 | 18 | 3963401 | 2407680 | 1555721 | 28 | 3982925 | 2457223 | 1525702 |
| 9 | 3971399 | 2448596 | 1522803 | 19 | 3951830 | 2420290 | 1531540 | 29 | 3964423 | 2407793 | 1556630 |

balanced (`fixed5_tps`, `no-backoff_tps`, `signed_difference_tps`):

| # | fixed5 | no-backoff | diff | # | fixed5 | no-backoff | diff | # | fixed5 | no-backoff | diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4266248 | 3839305 | 426943 | 10 | 4267886 | 3692540 | 575346 | 20 | 4238081 | 3636991 | 601090 |
| 1 | 4299728 | 3809857 | 489871 | 11 | 4234281 | 3675444 | 558837 | 21 | 4261385 | 3695365 | 566020 |
| 2 | 4287973 | 3827709 | 460264 | 12 | 4216400 | 3681928 | 534472 | 22 | 4238034 | 3688031 | 550003 |
| 3 | 4220740 | 3794193 | 426547 | 13 | 4238945 | 3637186 | 601759 | 23 | 4219884 | 3662701 | 557183 |
| 4 | 4280154 | 3784769 | 495385 | 14 | 4233314 | 3636034 | 597280 | 24 | 4213926 | 3634864 | 579062 |
| 5 | 4262007 | 3704651 | 557356 | 15 | 4231465 | 3719180 | 512285 | 25 | 4201613 | 3660731 | 540882 |
| 6 | 4284367 | 3710110 | 574257 | 16 | 4215761 | 3629000 | 586761 | 26 | 4264831 | 3651730 | 613101 |
| 7 | 4196713 | 3654921 | 541792 | 17 | 4262605 | 3675613 | 586992 | 27 | 4216717 | 3665513 | 551204 |
| 8 | 4245262 | 3682865 | 562397 | 18 | 4251757 | 3655718 | 596039 | 28 | 4224122 | 3716884 | 507238 |
| 9 | 4225692 | 3702883 | 522809 | 19 | 4245020 | 3658778 | 586242 | 29 | 4231982 | 3647252 | 584730 |

read-heavy (`fixed2_tps`, `no-backoff_tps`, `signed_difference_tps`):

| # | fixed2 | no-backoff | diff | # | fixed2 | no-backoff | diff | # | fixed2 | no-backoff | diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 9643112 | 10591731 | -948619 | 10 | 9633739 | 10158988 | -525249 | 20 | 9584380 | 10150430 | -566050 |
| 1 | 9721704 | 10234922 | -513218 | 11 | 9623978 | 10147882 | -523904 | 21 | 9575531 | 10129168 | -553637 |
| 2 | 9676249 | 10286507 | -610258 | 12 | 9614795 | 10134634 | -519839 | 22 | 9594491 | 10099378 | -504887 |
| 3 | 9648460 | 10188137 | -539677 | 13 | 9614667 | 10146126 | -531459 | 23 | 9582219 | 10145912 | -563693 |
| 4 | 9618108 | 10206272 | -588164 | 14 | 9638830 | 10196588 | -557758 | 24 | 9502119 | 10116236 | -614117 |
| 5 | 9661991 | 10172584 | -510593 | 15 | 9579939 | 10143617 | -563678 | 25 | 9591746 | 10115792 | -524046 |
| 6 | 9668916 | 10159708 | -490792 | 16 | 9607334 | 10126829 | -519495 | 26 | 9559084 | 10106564 | -547480 |
| 7 | 9658097 | 10168649 | -510552 | 17 | 9598621 | 10152730 | -554109 | 27 | 9497031 | 10083958 | -586927 |
| 8 | 9594208 | 10164129 | -569921 | 18 | 9591807 | 10155298 | -563491 | 28 | 9588564 | 10085779 | -497215 |
| 9 | 9622207 | 10174751 | -552544 | 19 | 9548396 | 10166462 | -618066 | 29 | 9607570 | 10155100 | -547530 |

(値は result.json の float を整数表記にしたもの。全 180 標本が整数値である。)

### 2.3 arm ごとの 30 標本の記述 (`arms.<name>.raw_tps` から本稿が計算した派生値。WAL `bench_done` の `median_tps` / `cv` は記録値)

| workload | arm | mean tps (派生) | min / max tps (派生) | median tps (WAL) | cv (WAL、標本 sd / 平均) | unstable | rounds | attempts |
|---|---|---:|---|---:|---:|---|---:|---:|
| write-heavy | fixed10 | 3,970,188.90 | 3,907,069 / 4,011,881 | 3971384.0 | 0.005909141675769404 | false | 1 | 1 |
| write-heavy | no-backoff | 2,431,737.43 | 2,326,624 / 2,730,303 | 2419811.0 | 0.0322747605417099 | false | 1 | 1 |
| balanced | fixed5 | 4,242,563.10 | 4,196,713 / 4,299,728 | 4238057.5 | 0.006212946185814447 | false | 1 | 1 |
| balanced | no-backoff | 3,694,424.87 | 3,629,000 / 3,839,305 | 3678770.5 | 0.01604910310303968 | false | 1 | 1 |
| read-heavy | fixed2 | 9,608,263.10 | 9,497,031 / 9,721,704 | 9607452.0 | 0.00495579129695054 | false | 1 | 1 |
| read-heavy | no-backoff | 10,168,828.70 | 10,083,958 / 10,591,731 | 10153915.0 | 0.008868175408282646 | false | 1 | 1 |

- 6 arm とも `expected_reps = observed_reps = 30`、`actual_rounds = 1`、`attempt_count = 1`、`unstable = false`、`high_variance = false`
  (WAL `commit`)、`rep_notes = []`、`valid = true`、`errors = []`。品質 gate (`aggregate_cv > 0.05` で unstable) には 6 arm とも掛かっていない。
- baseline (`no-backoff`) の cv は 3 workload とも variant より大きい (0.0323 / 0.0160 / 0.0089 対 0.0059 / 0.0062 / 0.0050)。これは観察であり、
  本稿はその理由を述べない。write-heavy の no-backoff は最初の対 (pair 0、物理順では最初の block の最初の rep) の 2,730,303 が 30 標本の最大値で、
  同 arm の 2 番目に大きい値 2,522,961 より 207,342 大きい。これも観察であり、外れ値としての除外・再計算は登録済み解析に無いので行わない。
- median は 5 標本 median を使う A-2 / A-6 と形式が違う (30 標本の中央値、WAL の `median_tps`)。本稿の推定量は median ではなく対差の算術平均であり、
  arm 単体の median は結果節の数値にしない。

### 2.4 正しさの記録 — campaign WAL の `verify_done` (性能の判定ではない)

3 本の WAL (`runs/wal.jsonl`、各 10 record: `build_start` / `build_done` / `verify_done` × 2 arm、`bench_done` × 2、`commit` × 2) の
`verify_done` 6 record:

| workload | arm (variant id) | commits | aborts | anomalies | certified | verdict | check config |
|---|---|---:|---:|---:|---|---|---|
| write-heavy | fixed10 (`a7f8486e1116`) | 458889 | 105711 | 0 | true | serializable | `legacy` |
| write-heavy | no-backoff (`84319b1127a6`) | 510621 | 197048 | 0 | true | serializable | `legacy` |
| balanced | fixed5 (`93c62227a2d3`) | 481088 | 133860 | 0 | true | serializable | `legacy` |
| balanced | no-backoff (`84319b1127a6`) | 509412 | 194033 | 0 | true | serializable | `legacy` |
| read-heavy | fixed2 (`82ea3a7b8618`) | 471051 | 166197 | 0 | true | serializable | `legacy` |
| read-heavy | no-backoff (`84319b1127a6`) | 523733 | 200282 | 0 | true | serializable | `legacy` |

- `proof_surfaces` は 6 record とも `{protocol: silo, X: evidence-present, P: evidence-present, I: evidence-absent}`、
  `commit_witness.commit_counts` は `commits` と一致、`batch_commit_counts` 0。
- result.json 側は `arms.<name>.correctness_evidence = {certified: [true], verify_configs: ["legacy"], verify_done_frames: [1 件]}` で、frame の
  `raw_sha256` と byte range で WAL の該当行を束縛する。`verify_done` 2 record の `payload.anomalies` は result.json の
  `workloads[].wal_evidence.records[]` に収録されており、上の表の値と一致する。
- **これは規律 2 の判定であって性能の判定ではない。** `certified` が言うのは、記録された `legacy` 検査条件の下で観測した YCSB point read/write
  trace の直列化可能性までであり、性能認証ではない。verify は trace-enabled build、bench は trace-disabled build で、別 build・別 run である
  (絶対規律 1)。attempt-0001 の `verify_done` (commits 459238 / 544423、466561 / 483318、516607 / 515988) とは trace が異なるので値は異なる。
  本稿はその差に意味を与えない。

### 2.5 時系列 (JST。WAL `ts`・receipt の epoch・成果物 mtime から換算。推定値なし)

| 時刻 | 事象 | 出所 |
|---|---|---|
| 18:10:34 | `authorize-rerun` rc 0 (認可 record 作成) | record file の mtime、本稿を書いた wave の job dir log |
| 18:11:15 → 18:11:16 | submit rc 0 (intent 18:11:15、submission 受領証 18:11:16、qstat 可視性 `QUE` 18:11:15) | intent / 受領証の mtime、`qstat-visibility.json` `observed_epoch` |
| 18:11:23 / 18:11:23 / 18:16:47 | job 開始 write-heavy / read-heavy / balanced (balanced は request 作成から 5 分 31 秒後。§1.4) | receipt `accounting.started_epoch_s`、`reservation_binding.scheduler_started_epoch` |
| 18:12:19〜18:13:22 | write-heavy と read-heavy の各 6 record (計 12 record): 各 arm の build (17〜18 秒) と verify (11〜13 秒)。write-heavy: fixed10 verify_done 18:12:48、no-backoff 18:13:22。read-heavy: 18:12:49 / 18:13:22 | WAL `ts` |
| 18:13:22 | ready barrier write-heavy / read-heavy | `barrier/ready/*.json` mtime |
| 18:17:42〜18:18:44 | balanced の build と verify: fixed5 verify_done 18:18:11、no-backoff 18:18:44 | WAL `ts` |
| 18:18:44 | ready barrier balanced、bench-go、bench-start 3 本 (最後の ready の直後) | `barrier/ready/balanced.json` / `bench-go.json` / `bench-start/*.json` mtime |
| 18:18:44 → 18:22:07 | balanced の bench (rep 30 対、`schedule_wall_s` 202.64) → bench_done / commit 18:22:07 | schedule receipt `reps[].started_at_ns` / `ended_at_ns`、WAL `ts` |
| 18:22:07 → 18:25:29 | read-heavy の bench (`schedule_wall_s` 404.95 = bench lock 待ち約 202 秒 + 自身の bench) → bench_done / commit 18:25:29 | 同上 |
| 18:25:29 → 18:28:51 | write-heavy の bench (`schedule_wall_s` 607.07) → bench_done / commit 18:28:52 | 同上 |
| 18:22:08 / 18:25:31 / 18:28:53 | job 終了 balanced / read-heavy / write-heavy (driver rc 0 / shell rc 0 / status finished) | receipt `accounting.ended_epoch_s`、`jobs/<w>/job-terminal.json` |
| 18:30:05 → 18:30:06 | complete rc 0 (receipt `recorded_epoch` 18:30:05) | job dir log の時刻、receipt.json |
| 18:30:21 | materialize rc 0 (公開 leaf 4 file、兄弟 dir) | job dir log の時刻、leaf の mtime |

- 3 workload の bench 相は重ならず、balanced → read-heavy → write-heavy の順に走った (policy の bench lock、`bench_lock_acquisitions_per_workload` 1。
  各 workload の `schedule_wall_s` が約 202 / 405 / 607 秒と階段状になっているのは lock 待ちを含むため)。attempt-0001 の順は read-heavy →
  write-heavy → balanced (schedule_wall_s 201.51 / 403.14 / 604.24) であり、**bench 相の順序は attempt 間で異なる**。これは観察であり、本稿は
  順序の影響を推定しない (§3 L-A1S2-9)。`bench_wall_s` (arm ごとに 100.87〜101.24 秒) は attempt-0001 (100.4〜100.8 秒) と同程度である。
- `settled` (settle 時の load1): write-heavy 0.038、balanced 1.610、read-heavy 0.000 (threshold 4.0、3 本とも `settled: true`)。
  attempt-0001 は 0.027 / 0.023 / 2.257。競合テナント probe は fail-closed で、3 workload とも abort していない (`errors=[]`)。
- 再投入は行われていない (認可は attempt-0002 の 1 attempt。落ちていないので再走の要否は生じていない。事前登録 §6.4 と追補は性能値を再投入・
  3 本目の理由にしない)。

### 2.6 図

本稿の時点で attempt-0002 の図は無い。attempt-0001 の fig9 (`figures/fig9_a1_balanced5_sized_attempt1.*`) は attempt-0001 稿を
`caption_source` として束縛する凍結物であり、本稿の値を含まない。図の作成と束縛方式は本稿を書いた wave の対象外である
(本稿は図の provenance の hash を持たない、F36)。

### 2.7 attempt-0001 稿との並記 (プールしない。差・比・合成区間・再現判定を書かない)

attempt-0001 の値は公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized/result.json` (sha256 `372f199e…`) の
`workloads[].statistics` から逐語で転記した (attempt-0001 稿 §2.1 とも一致する)。attempt-0002 の値は §2.1。**2 行は独立した 2 つの観測であり、本稿は 2 行から何も計算しない。**

| workload | attempt | 投入 (JST) | source commit | node | mean (variant − baseline) tps | h tps | descriptive interval tps | B tps | baseline mean tps | sample sd / planned sigma | classification | variance_plan_breach |
|---|---|---|---|---|---:|---:|---|---:|---:|---|---|---|
| write-heavy | attempt-0001 | 2026-09-18 06:30 | `d2ebef7a4` | bnode107 | `1591948.5` | `23911.502943472762` | `[1568036.9970565273, 1615860.0029434727]` | `68795.219` | `2293173.966666667` | `46253.31396347129` / `66403.45210801972` | `resolved-above-floor` | `false` |
| write-heavy | attempt-0002 | 2026-09-20 18:11 | `fec4a8187` | bnode035 | `1538451.4666666666` | `41434.211082207854` | `[1497017.2555844588, 1579885.6777488743]` | `72952.12299999999` | `2431737.433333333` | `80148.43644687126` / `66403.45210801972` | `resolved-above-floor` | `true` |
| balanced | attempt-0001 | 2026-09-18 06:30 | `d2ebef7a4` | bnode108 | `448830.1666666667` | `28351.599461068836` | `[420478.5672055979, 477181.7661277355]` | `115876.89600000001` | `3862563.2` | `54842.032905228465` / `56697.43571357468` | `resolved-above-floor` | `false` |
| balanced | attempt-0002 | 2026-09-20 18:11 | `fec4a8187` | bnode039 | `548138.2333333333` | `25552.384438113106` | `[522585.8488952202, 573690.6177714464]` | `110832.746` | `3694424.8666666667` | `49427.359824489315` / `56697.43571357468` | `resolved-above-floor` | `false` |
| read-heavy | attempt-0001 | 2026-09-18 06:30 | `d2ebef7a4` | bnode109 | `-576749.7666666667` | `32963.69867738655` | `[-609713.4653440532, -543786.0679892802]` | `310204.40199999994` | `10340146.733333332` | `63763.46597396226` / `74668.48956627495` | `resolved-above-floor` | `false` |
| read-heavy | attempt-0002 | 2026-09-20 18:11 | `fec4a8187` | bnode040 | `-560565.6` | `41746.744315864176` | `[-602312.3443158641, -518818.8556841358]` | `305064.861` | `10168828.7` | `80752.98639149407` / `74668.48956627495` | `resolved-above-floor` | `true` |

- 並記から本稿が書けるのは次の事実命題までである: (a) 登録済み解析の分類は 2 attempt × 3 workload の 6 cell すべてが `resolved-above-floor`、
  (b) 対差平均の符号は 3 workload とも 2 attempt で同じ (+ / + / −)、(c) `variance_plan_breach` は attempt-0001 が 3 本とも false、attempt-0002 が
  write-heavy / read-heavy で true。**これらは観察であり、「再現した」「安定している」「差がある」の判定ではない。** 2 attempt の区間の重なり・
  平均の差・比を本稿は計算せず、そのための事前登録も存在しない (事前登録 §5 は 1 attempt 内の 30 対に対する規則である)。
- 2 attempt は同じ policy・同じ root seed・同じ物理順 (§1.5) だが、node・時刻帯・bench 相の順序・source commit (driver の gate 部分) が異なる。
  どの差がどの値の差に効いたかを本稿は帰属しない。
- attempt-0001 稿の限定 L-A1S-4 (単一 attempt を反復間の安定性へ一般化しない) は attempt-0001 稿の凍結物として残る。attempt-0002 が存在する
  ことで L-A1S-4 をどう扱うかは、追補が定めるとおり本稿の外の裁定に属する。

---

## 3. 限定 (この結果が言わないこと)

attempt-0001 稿の L-A1S-1〜L-A1S-20 を参照する。ただし次の読み替えの下で参照する — L-A1S-4 (単一 attempt) は本稿 L-A1S2-3 / L-A1S2-4、
L-A1S-16 の測定 node は bnode035 / 039 / 040 (時刻帯 18:11〜18:29 JST)、L-A1S-18 は本 attempt に図が無い (L-A1S2-11)、L-A1S-20 の時刻は本稿 §2.5。
attempt-0001 稿の本文・判定は変更しない。本稿はそれらを再掲せず、attempt-0002 と並記に固有の限定を足す。

| # | 限定 | 出所 |
|---|---|---|
| L-A1S2-1 | **非認証 lane の結果である。** `formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only` は結果を見た後も動いていない。追補も認可 record もこの lane を変えない | policy `authority`、事前登録 §1.1 / §7.2、追補「限界」 |
| L-A1S2-2 | **headline 値にしない。** 論文の主張の数値にこの attempt の値を置かない。「A-1 の値がある」と書けるかどうかは本稿の外の裁定である | 本稿の利用範囲 (§0.3)、D2044 項 8 / D2120 項 3 / D2172 項 2 |
| L-A1S2-3 | **並記は再現判定ではない。** §2.7 の 6 cell の分類と符号の一致は観察であり、「再現した」「安定している」とは書かない。2 attempt をプールした推定量・差・比・合成区間は作らない。attempt 間の比較のための事前登録は存在しない | D1993 項 6、事前登録 §5 (1 attempt 内の規則)、追補「限界」 |
| L-A1S2-4 | **L-A1S-4 (反復間の安定性への一般化禁止) の解除可否を本稿は判定しない。** 本稿は 2 本目の観測を提供するだけである | 追補「保存する登録」、D2172 項 2 |
| L-A1S2-5 | **認可 record は電子署名ではなく、認可者が attempt-0001 の性能値を見た後に再現を選んだかどうかを識別しない。** record と self digest は破損検出である。attempt-0002 は attempt-0001 の結果 (2026-09-18) が公開された後に裁定・認可・投入された | D2172 項 2、追補「限界」、D2178 |
| L-A1S2-6 | **3 本目の attempt の認可・要否を言わない。** 認可は attempt-0002 の 1 attempt 限りで、attempt-0003 には改めて裁定・定数・record が要る。本 attempt の性能値・`variance_plan_breach` は再投入・3 本目の理由にならない | 追補 §6.4 項 4・項 5、事前登録 §6.4 |
| L-A1S2-7 | **source commit は attempt-0001 と異なる。** 束縛 9 file のうち driver 1 本が 143 行 (認可 record の生成・照合、submit / materialize への接続、CLI 分岐) 違う。推定量・分類・測定経路の関数に変更行が無いことは静的に確認しただけで、実行時に等価性を検証していない | §1.5、§4.3、`git diff d2ebef7a4 fec4a8187` |
| L-A1S2-8 | **`variance_plan_breach = true` (write-heavy / read-heavy) の原因を帰属しない。** 標本 sd が計画 sigma を超えたことは記録値であり、node・時刻帯・bench 順・baseline arm の最初の対 (write-heavy no-backoff の 2,730,303) のいずれに帰属するかを本稿は言わない。事前登録は breach 時の扱い (再走・除外・再計画) を定めていないので、本稿もそれを定めない | §2.1、§2.3、事前登録 §5、policy `sizing` |
| L-A1S2-9 | **3 workload の bench 相の順序 (balanced → read-heavy → write-heavy) が attempt-0001 (read-heavy → write-heavy → balanced) と異なることの影響を推定しない。** 各 workload は別 node で走り、順序は bench lock の獲得順で決まった。順序が値に効いたかどうかは本 attempt から言えない | §2.5、policy `execution.bench_lock_*` |
| L-A1S2-10 | **balanced の scheduler 待ち (Pre-running 5 分 31 秒) と node の違い (bnode035 / 039 / 040 対 107 / 108 / 109) の影響を推定しない** | §1.4、receipt `reservation_binding` |
| L-A1S2-11 | **図は無い。** attempt-0002 の図と 2 attempt の並記図は本稿の時点で存在せず、fig9 は attempt-0001 の図である | §2.6 |
| L-A1S2-12 | **公開 leaf の公開先 (兄弟 dir) は attempt-0001 の leaf と別で、attempt-0001 の leaf には何も書き足していない。** publish は非協力的な書き手に対して原子的な no-replace ではない (attempt-0001 と同じ fallback) | `.complete.json` `publish.limitations`、追補 §6.1 |
| L-A1S2-13 | **投入から materialize 完了までの約 20 分 (18:10:34 〜 18:30:21) は再投入の予算や計画値ではない。** balanced の scheduler 待ちを含む | §2.5 |

---

## 4. 欠落 — 権威 bytes・WAL・事前登録・裁定の対応が確かめられない箇所

### 4.1 成果物に情報が無い

- `legacy` 検査条件の実引数 (attempt-0001 稿 L-A1S-10 と同じ)。
- verify の trace-enabled build の識別子 (`trace_bin_sha256`) は WAL `build_done` にあるが、本稿は 6 本の値を転記していない
  (正しさ証拠の同一性は `verify_done_frames` の `raw_sha256` が WAL 行を束縛する形で result.json が持つ)。
- perf は使っていないので、cache miss 率・IPC は存在しない (欠落ではなく設計)。
- balanced job の `Pre-running` 5 分 31 秒の理由 (scheduler 側の事情) は成果物に無い。

### 4.2 束縛の範囲が限られる

- 公開 leaf の `result.json` (`b7e0518e…`、269786 bytes) は raw の `raw/results/result.json` (`c9031faa…`、263459 bytes) と bytes が異なる。差は
  materializer が足した `materialization_evidence` と `limitations` 5 項目め (publish fallback) だけで、`workloads[].statistics` と `arms` は
  構造比較で同一である (本稿の作成時に照合)。receipt.json の `result.sha256` と `materialization.raw_result.sha256` は raw を指す。
  **本稿の数値は公開 leaf から取り、raw との同一性は本稿の作成時の照合に依る。**
- source binding の 9 file は `git_blob_oid` と `working_sha256` で束縛されるが、投入 worktree が detached であることと tracked-clean の検査は
  成果物の外 (job preflight、本稿を書いた wave の job dir) に記録がある。
- 認可 record の束縛は source commit 経由であり、追補 file 自身の実行時 digest 検査は無い (追補「機械可読の束縛」)。

### 4.3 本稿で対応を再確認していない

- `balanced-schedule-receipt.json` (3 本、sha256 は result.json `schedule_receipt` と一致することを照合した) の seed からの bit 導出と物理順の
  再現は本稿では行っていない。本稿が確かめたのは `root_seed` / `effective_root_seed` / `seed_counter` / `group_bits` / `blocks[].arm` が
  attempt-0001 の receipt と一致することまでである。
- campaign.lock の `identity_preimage` は attempt-0001 と 4 箇所 (`intent_sha256` / `source_binding_sha256` / `source_commit` / `identity_tag`) だけ
  異なることを構造比較したが、`build_admission` の中身は照合していない。
- driver の差分 143 行について、測定・統計関数自身に変更行が無いことを静的に確認した。実行時の等価性 (同一入力での実行結果比較) は検証していない。
- job stdout / stderr (各 875〜885 / 556〜557 bytes) の全文は本稿の照合に使っていない。

---

## 5. 一次資料

### 5.1 権威 bytes と転記元 (repo 内、tracked) — `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/`

本稿の作成時 (2026-09-20) に現物 bytes から再計算した SHA-256。materializer が submit-tree に排他作成した 4 file を byte 保持で複製したもので、
`.complete.json` の `files` map と一致する。

| file | SHA-256 | bytes |
|---|---|---:|
| `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/result.json` | `b7e0518e197500f2daf875e841acabf63f5eddb82bc14e072dd28e3431fe5f74` | 269786 |
| `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/receipt.json` | `98c35cca4fe0e9f12559b8f9dc3acb4c6c5c4c597e5f5cc01a6449533918ecbf` | 19393 |
| `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/README.md` | `034cd1fd2f5004b1faac27d7e5e629a88c29f1e89dfd5fd1af9e6eadc50b53a1` | 3284 |
| `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/.complete.json` | `7ad34232eaf920babd783140c47018b5c9d2f7665635872d4c2ee3be6f464fb3` | 1407 |
| `orchestrator/campaign/paper_story_a1_paired.v3-sized.json` | `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a` | (policy。result.json `policy_sha256` と一致) |

- `.complete.json` の `files` map: README.md `034cd1fd…`、receipt.json `98c35cca…`、result.json `b7e0518e…` (上と一致)。schema
  `paper-story-a1-paired-materialization-complete/v1`、publish 機構 `a1-exclusive-claim-check-then-renameat2` (`RENAME_NOREPLACE` が EINVAL の
  fallback)、`destination` は submit-tree 内の兄弟 dir の絶対 path。
- 公開 leaf の `README.md` (materializer の出力) は §2.1 の表を 6 桁固定小数で持つ (`1538451.466667` 等)。本稿は result.json の float を逐語で
  写した (`README.md` を出所にしていない)。
- 最上位 `authority` は schema v3 の固定値 `exploratory` (materializer の契約) で、policy の `result_authority`
  (`sized-preregistered-descriptive-only`) とは別欄である。

### 5.2 durable authority (repo 外) — `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/`

本稿の作成時に現物から再計算し、result.json の記録値 (sha256 と bytes) と一致することを確認した。

| workload | file | SHA-256 | bytes |
|---|---|---|---:|
| write-heavy | `jobs/write-heavy/raw/campaign-output/exploration/campaigns/paper-story-a1-write-heavy-paired-ec74e1c8/campaign.lock` | `0ec558982139d68cbfb03372ee1d854b6236ff497d2d05f36cef8f28d19f6716` | 5463 |
| write-heavy | 同 `…/runs/wal.jsonl` | `173a0060ccc20ab1092790b193a6e0c805277ae72c1119d57de7590a79f7228e` | 17942 |
| write-heavy | 同 `…/balanced-schedule-receipt.json` | `cbd853fc34da4383f5d9c7ee0890e3f104ed405224a2971a6528b343f0a6b606` | 12943 |
| balanced | `jobs/balanced/raw/campaign-output/exploration/campaigns/paper-story-a1-balanced-paired-fdd1cb88/campaign.lock` | `e68c85ce44e628b4a6645b1b413cdb5968a399bfc6e4c8e488c036d1c9ed74b6` | 5433 |
| balanced | 同 `…/runs/wal.jsonl` | `8cc4bc23c5c64ea8a992a5d95c734c5863e7335b1a1c0d20c134339968e89065` | 17871 |
| balanced | 同 `…/balanced-schedule-receipt.json` | `bc65d939927d43691a0c915183fcb14cff8fe6948757676b1acbf50e1ee96052` | 12907 |
| read-heavy | `jobs/read-heavy/raw/campaign-output/exploration/campaigns/paper-story-a1-read-heavy-paired-9912d892/campaign.lock` | `b814513dbc274090abc57329864d3a1b197331b5542ade373c8753068319333d` | 5447 |
| read-heavy | 同 `…/runs/wal.jsonl` | `eb1f3234ae5ea61326e310b6cfc4b3e292f89f25d6a9bdfebcb4ac83085aed7b` | 17953 |
| read-heavy | 同 `…/balanced-schedule-receipt.json` | `a2d5d037648beb1b34d438a0ce7ff9f8ebe15493000d50902e98bb9fbaba8632` | 13004 |

- raw results: `raw/results/result.json` `c9031faa9442974af344b54c6b700c58f5decb4d1447e4fb6bc16e6373bbee96` (263459 bytes)、
  `raw/results/receipt.json` `f06a2bc811b55ec720bb0224c673b1b086593cebb554d9d1b844b3834eedb355` (18147 bytes) (§4.2 のとおり公開 leaf とは
  bytes が違う)。
- 受領証: `receipts/submission.json` `7fb0ebd66652d4d91cf399d2fa5b523b90615f0c493c4275f089ba1a8561aeb6` (12982 bytes)、`receipts/completion.json`
  `11202bf73f4ad15c84bf46047c0f990b0c5f5f9cb3631819bd301e7d38c648ea` (5102 bytes)、`raw/job-terminal.json`
  `a9bc5f9a150533fd3900140bd2dea1b307c9706e2862158a3a98499a6af6cb38` (3013 bytes)、intent `attempt-0002.intent.json`
  `5a66484d6c65e15d22544cd54c9116547e9fee0418df33d88d69332a191ff3db` (14124 bytes、base 直下)、認可 record `attempt-0002.authorization.json`
  `8204f9759e51fc2b357fbad5d7edaf5464974fc1cee2e4862749d4598c43d685` (501 bytes、base 直下)。いずれも本稿を書いた wave の insight
  (`output/insights/2026-09-20/t2792-a1-sized-attempt2/`) に複製と sha256 がある。
- campaign id: `paper-story-a1-write-heavy-paired-ec74e1c8` / `paper-story-a1-balanced-paired-fdd1cb88` / `paper-story-a1-read-heavy-paired-9912d892`
  (`recomputed_campaign_id` と一致。attempt-0001 と同じ id だが campaign.lock の bytes は異なる)。WAL の `env_tag` は 3 本とも `pegasus`、
  `line_issues = []`、`truncated_tail = false`。

### 5.3 repo 内 (tracked) の一次資料

- 事前登録 `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md` (§1.1 の sha256)。
- 追補 `output/insights/2026-09-20/t2792-a1-sized-preregistration-amendment/README.md` (§1.4 の sha256、commit `ec696308a`)。
- policy `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`、実装 `orchestrator/campaign/paper_story_a1_paired.py`
  (`_classify_difference`、`_statistics_from_signed_differences`、`_assert_no_prior_v3_bench_start`、`_exact_v3_rerun_authorization`、
  `_exact_materialization_destination`、`run_authorize_rerun`)、source 契約 `orchestrator/campaign/paper_story_a1_source.v2.json`、source 追補
  `output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md`、patch `patches/silo-backoff-fixed.patch`、job body
  `tools/pegasus/paper_story_a1_paired.sh` (いずれも result.json `source_binding.files` の 9 本に含まれる。measurement source commit
  `fec4a818741e5464fffcd11e4b094c125dfe5280`)。
- attempt-0001 の公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized/` (§2.7 の並記の出所。result.json sha256 `372f199e…`) と
  attempt-0001 稿 `docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`。
- 認可 gate の実装 wave の insight `output/insights/2026-09-20/t2792-a1-sized-rerun-authorization/README.md` (D2178 の実測・変異台帳)。
- 本稿を書いた wave の insight `output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md` (投入・時系列・受領証の複製・検算の逐語・レビュー)。

### 5.4 裁定

- D2172 項 2 (2026-09-20、択 1 を attempt-0002 の 1 attempt 限定で認可、研究目的 = 同一配置の反復)、D2178 (認可 gate の設計)、D2156 (2026-09-19、
  gate を緩めずに裁定パッケージへ返した)、D2120 項 3 (attempt-0001 の認可)、D2044 項 8 / D1986 項 5 (認可の据え置きとユーザー手番)、D1262
  (estimand の揃え直し)、D1631 (results 系列の規則)、D1993 (再現判定の区別、項 6 のプール禁止)、D1637 (2 本目の論文と共用しない)、D12
  (protocol status を成否の宣告へ拡張しない)、D2120 項 15 (単独 results 稿の型 = [T-2611] / [T-2674])。

### 5.5 値の出所 (転記した数値ごと)

| 数値 | 出所 |
|---|---|
| §2.1 / §2.7 (attempt-0002 行) の mean / h / 区間 / B / baseline mean / sd / planned sigma / k / df / 分類 / breach | result.json `workloads[].statistics` (逐語) |
| §2.7 の attempt-0001 行 | attempt-0001 の公開 leaf result.json (`372f199e…`) の `workloads[].statistics` (逐語。attempt-0001 稿 §2.1 と一致) |
| §2.2 の 180 標本と 90 対差 | result.json `workloads[].statistics.pairs` |
| §2.3 の mean / min / max、§2.1 の sd / sigma 比と mean / bmean 比 | result.json `arms.<name>.raw_tps` / `statistics` から本稿が計算 (派生値) |
| §2.3 の median / cv、§2.4 の commits / aborts / anomalies / verdict、§2.5 の WAL 時刻と `bench_wall_s` | 各 workload の `runs/wal.jsonl` (`bench_done` / `verify_done` / `ts`) |
| §1.5 / §2.5 の seed / group_bits / block 順 / `schedule_wall_s` / `settled` / rep の開始・終了時刻 | 各 workload の `balanced-schedule-receipt.json` (`document`) |
| §1.4 の request / host / elapsed / CPU / 時刻、scheduler terminal | receipt.json `job_executions` (`accounting`、`reservation_binding`)、completion 受領証 |
| §1.4 の認可 record の内容 | `attempt-0002.authorization.json` (逐語) |
| §1.4 / §2.5 の authorize-rerun / submit / complete / materialize の時刻、balanced の `Pre-running` | 本稿を書いた wave の job dir file (`*.log` / `*.done` / record・intent・受領証の mtime) と投入時の `qstat -f` 観測。本稿はこの時刻を再計測していない |
| §1.1〜§1.3 の条件 | policy v3-sized.json、事前登録 README、WAL `build_start.genome` / `bench_done.run_cmd` |
| §1.5 の driver 差分の所属関数 | `git diff -U0 d2ebef7a4 fec4a8187 -- orchestrator/campaign/paper_story_a1_paired.py` の new 側行番号を新版 file の AST (関数の行範囲) で帰属 |
| §5.1 / §5.2 の sha256 と bytes | 本稿の作成時に現物から再計算 |

### 5.6 同じ結果についての既存の記述 (本稿の出所ではない)

- `docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」の 2026-09-19 の注記 (A-1 sized attempt-0002 の 1 attempt 認可と
  既存 gate による拒否) — 本稿の投入以前の状態を指す stale 注記であり、本稿の時点では「認可 record 経由で投入され完走した」に置き換わる
  (置き換えは版が行い、本稿は行わない)。
- `docs/paper-story/2026-09-20.md` §0 / §2 の A-1 項 — 執筆時点 (attempt-0002 は gate 拒否で未投入) の記述で、凍結物として残る。
- `output/insights/2026-09-19/a1-sized-attempt2/README.md` — attempt-0002 が gate で拒否された 2026-09-19 の記録と裁定パッケージ (択 1〜3)。
  本稿はそこから数値を取っていない。
- `docs/paper-story/claim-evidence/2026-08-26.md` の A-1 行と `L23` — 旧 policy v2 (`static10 − adaptive`) 前提の凍結物で、D1262 以後の study と
  本 attempt を反映していない。

---
