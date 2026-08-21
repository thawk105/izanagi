射影対象はすべて読めた。read-onlyで照合し、コード変更・commit・pytest実走は行っていない。

# 暫定判定

(P2) は支持される。ただし、brief の表現には2点修正が必要である。

1. 「評価器経路が1本も無い」は、厳密には「充足を返す経路が1本も無い」と読むべきである。7条件は評価器へ dispatch されるが、充足証明を返さず、`SATISFIABLE_CONDITION_IDS` も空である。

   `docs/phase3-8c-preregistration.md:303-317`  
   `docs/phase3-8c-preregistration.md:328-337`

2. H1/H2 の定義・arm digest の実装足場は現行コードに存在する。正式起動を拒む直接の根拠は、effective preregistration が無く、`_preflight_workload_profile()` が明示的に拒否することである。

   `orchestrator/campaign/p3_autonomous_workload_trial.py:218-252`  
   `orchestrator/campaign/p3_autonomous_workload_trial.py:817-896`

## 1. (P2) の一次資料照合

| brief の主張 | 照合結果 |
|---|---|
| §5 は9項目中8項目が未記入 | 正確。`docs/phase3-8c-preregistration.md:185-197` は9行あり、検定4点だけが記入済み、残り8行が `未記入`。 |
| §6 の12条件に充足を返す経路がない | 実質的に正確。ただし7条件は dispatch 対象であり、0件なのは「充足証明を返す経路」。`docs/phase3-8c-preregistration.md:199-265,303-317`。C07追随後も `SATISFIABLE_CONDITION_IDS` は空。`docs/phase3-8c-preregistration.md:328-337` |
| §7 は現行productionで実行不能と明記 | 正確。`docs/phase3-8c-preregistration.md:497-527`、特に `:520-523`。 |
| 8b floor判定は仕様のみ発効 | 正確。paired差分、attempt registry、judge追随前は測定不可。`docs/phase3-8b-descriptor-design.md:424-437,441-484,518-555`。 |
| 現行コードからも正式起動不可 | 正確。formal profile の検証後に `effective preregistration unavailable` で停止する。`orchestrator/campaign/p3_autonomous_workload_trial.py:883-896`。runbookもH1/H2を無条件拒否する。`docs/phase3-s8c-autonomous-trial-runbook.md:61-72` |

なお、brief の「第8世代 `s8c-decider/v4`」という epoch 表記は要再確認である。文書本文は第8世代/v4を記載しているが、作業木には後続らしい g9/v5 と g10/v6 が存在し、g10は `s8c-decider/v6` を名乗っている。

`output/insights/2026-08-21_t1472-h1h2-readiness-audit/brief.md:18-20`  
`docs/phase3-8c-preregistration.md:328-337`  
`output/s8c-preregistration/condition-freeze/condition-freeze.v1.g10.json:1`

## 2. brief の確定済み裁定・事実

| 項目 | 照合 |
|---|---|
| 2026-07-16 H1/H2 承認 | 正確。H1=rr80、H2=rr20、skew=0.9、rmw=0、1m/48 threads。`docs/phase3-8b-descriptor-design.md:3-12,113-127`。実 artifact も `confirmed_at=2026-07-16` で、floor/budgetはnull。`output/s8b-freeze/holdout_freeze.json:616-624` |
| on/off/swapped | 正確。`on` は正しいdescriptor、`off` は中立入力、`swapped` はderangement先のdescriptor。`docs/phase3-8b-descriptor-design.md:156-173` |
| 2026-08-10 scope-B | 正確。scope-B再開、Q3 guard、T-139走行中の投入抑制、T-139優先が明記されている。`docs/phase3-8b-restart-runbook.md:1-7,19-28`。第1世代内でfloor pilotを行う裁定も `:330-348` にある。 |
| 2026-08-18再凍結 | 正確。ただしD496本体の日付は2026-08-17で、8/18の再凍結は `[T-1336]/[T-1337]` による実施形である。`docs/decisions.md:20614-20626`、`docs/decisions.md:21225-21260`、`docs/phase3-8b-descriptor-design.md:424-437` |
| paired差分への変更 | 正確。同一holdout・同一反復添字の対差、有限平均、標本SDを使い、floor超過を主判定から外す。`docs/phase3-8b-descriptor-design.md:439-480` |
| 2026-08-20 T-425 | 正確。ただしT-424/T-272は「実装ゼロ」ではなく部分実装で未閉包。公式H1/H2起票は要求閉包またはD145決定5再訪、かつrr80/rr20 calibration登録まで不可。`docs/archive/worklog-phase3-0820-731.md:121-134`、`output/insights/2026-08-20_t425-dependency-reaudit/README.md:63-91,156-176` |
| D581の影響 | briefに補足が必要。D581は公式 `s8b_floor_campaign.py` の事前登録儀式を緩和したが、T-425の `between_run_floor.py` への機械的適用は未検証。`docs/decisions.md:23453-23482`、`output/insights/2026-08-20_t425-dependency-reaudit/README.md:55-61` |
| D356 | 正確。機械が確認できるのはstaged diffの人間reviewまでで、承認者の人間性は機械強制されない。`docs/decisions.md:15565-15587` |

brief の(P3)については、worklog上の持ち越しは確認できるが、射影資料だけでは `ListAgents` の「稼働中」までは検証できない。現在のworklogでは、T-425、T-972、T-1371、T-1438、T-1458が次の一手として継続している。

`docs/worklog.md:2858-2865`  
`docs/worklog.md:2944-2947`  
`docs/worklog.md:3093-3096`  
`docs/worklog.md:3301-3304`  
`docs/worklog.md:3346-3349`  
`docs/worklog.md:3394-3397`

## 3. T-1472 command 引数に対する監査プラン

### (a) H1/H2、on/off/swapped の定義と実装

- 定義の正本は `docs/phase3-8b-descriptor-design.md:113-127,156-173`。
- module上のH1/H2は `rr80`/`rr20`、1m/48 threadsとして存在する。`orchestrator/campaign/s8b_holdout_freeze.py:80-112`
- p3にも `FORMAL_WORKLOADS`、scale検査、arm digest bindingの足場はある。`orchestrator/campaign/p3_autonomous_workload_trial.py:235-242,710-793,817-846`
- しかしcampaign identityには常に `pilot_scope="exploratory-ycsb-abc"` が入り、spec本文もformal claimを否定している。`orchestrator/campaign/p3_autonomous_workload_trial.py:722-752`
- 最終的にformal profileは `effective preregistration unavailable` で拒否される。`orchestrator/campaign/p3_autonomous_workload_trial.py:883-896`

段3では、CLI → `run_trial()` → launch admission → profile preflightの順に追い、H1/H2 scaffoldが正式実験へ到達しないことを確認する。arm digestの存在だけを正式実験実装完了と扱わない。

### (b) holdout定義と凍結状況

- holdout定義・未知性確認・positive controlは `docs/phase3-8b-descriptor-design.md:106-129`。
- v1 freeze生成は `--confirmed-by` / `--confirmed-at` を要求する。`orchestrator/campaign/s8b_holdout_freeze.py:808-868`
- `output/s8b-freeze/holdout_freeze.json` は存在し、H1/H2、derangement、human confirmationはあるが、`floor=null`、`budget=null`。`output/s8b-freeze/holdout_freeze.json:616-624`
- `verify` はholdout実走後に未知性hitが出るため、再実行でfail-closedになる仕様。`orchestrator/campaign/s8b_holdout_freeze.py:985-1035`

段3では、freeze hash、selector predictionの参照hash、現行HEADの未知性scan、v2 candidateの有無を別々に確認する。

### (c) rr80/rr20 calibration

現状は未充足。

- T-425再監査は、登録済みcalibrationがrr50であり、rr80/rr20向けが未登録と記録している。`output/insights/2026-08-20_t425-dependency-reaudit/README.md:22-26,34-61`
- oracle v2実走前にはverified calibration、contract一致、attestation receiptが必須。`orchestrator/campaign/s8b_oracle_driver.py:910-978`
- g1→g2の環境契約活性化はhuman lockstep待ち。`docs/decisions.md:22358-22366`、`docs/decisions.md:18175-18186`

段3では、H1/H2 calibration artifact → `calibration_ref` → attestation receipt → human activationの4段を一本の証拠鎖として追う。

### (d) floor/oracle prerequisite

- 現行oracle gateは`floor-null`と`budget-null`を返す状態。`docs/phase3-8b-restart-runbook.md:32-52,122-144`
- freeze v2 candidateのproducer自体が不在で、oracle manifestもproduction callerがない。`docs/phase3-8b-restart-runbook.md:258-275`
- oracle `run-block` はmanifest必須で、active ratified freeze、manifest、binary store、calibration、budgetを要求する。`orchestrator/campaign/s8b_oracle_driver.py:1256-1399,1829-1894`
- 8c側でもpaired judge、3表、parameter validator、floor artifactを判定入力にしない規則が未接続。`docs/phase3-8c-preregistration.md:231-239`
- D538はfloor artifactを出所検証に限定し、judge入力にしないと定める。`docs/decisions.md:22076-22090`

D581によるfloor儀式緩和を、T-425のgeneric scalarや8c paired floorの充足と混同しない。

### (e) 必要なhuman lockstep

明示的に必要なものは次のとおり。

1. holdout生成時の確認者・確認日時。`orchestrator/campaign/s8b_holdout_freeze.py:817-820`
2. rr80/rr20 calibrationの登録とg1→g2 activation。`docs/decisions.md:18175-18186,22358-22366`
3. T-424/T-272全閉包、またはD145決定5の明示的再訪。`docs/archive/worklog-phase3-0820-731.md:127-134`
4. paired judgeの `n` / `delta_min` / `sd_max` を結果閲覧前に確定し、judge実装後に8b再凍結・承認すること。`docs/phase3-8b-descriptor-design.md:466-484`
5. 6-cell manifest、schedule、registry、二段commit bindingの確定。`docs/phase3-8c-preregistration.md:213-265,497-519`
6. oracle specについては、機械承認ではなく人間のstaged diff reviewまでしか機械的に表現できない。`docs/decisions.md:15567-15587`
7. scope-BのQ3運用guard（単独性、T-139非稼働、裁定優先順位）。`docs/phase3-8b-restart-runbook.md:19-28`

### (f) 期待artifact

read-only inventoryの結果は次のとおり。

存在するもの:

- `output/s8b-freeze/holdout_freeze.json`
- `output/s8b-freeze/floor_protocol.json`
- `output/s8b-freeze/selector_predictions.json`
- `output/s8c-preregistration/arm-inputs/freeze.v1.json`
- `output/s8c-preregistration/arm-inputs/off-neutral-descriptor.v1.json`
- `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1.json` 〜 `g10.json`

selector predictionはfreeze hashを参照している。`output/s8b-freeze/selector_predictions.json:1-12`

不足・不在のもの:

- `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`
- `output/s8b-freeze/holdout_freeze.v2.g1.json`
- `output/s8b-freeze-budget-approvals/g1.json`
- `output/s8c-preregistration/schedule.v1.json`
- `output/exploration/autonomous-trials/`
- `output/autonomous-trials/`

v2 candidateのpath自体が、実装定数では `output/s8b-freeze-candidates/...`、restart runbookでは `output/s8b-freeze/holdout_freeze.v2.g{N}.json` と食い違う。

`orchestrator/campaign/s8b_holdout_freeze.py:47-61`  
`docs/phase3-8b-restart-runbook.md:258-268`

また、briefのv4表記に対してg10 artifactはv6を名乗るため、active generationの解決を別途行う必要がある。`output/s8c-preregistration/condition-freeze/condition-freeze.v1.g10.json:1`

### (g) exact submission command

現在存在するのは部品コマンドであり、正式H1/H2のsingle exact submission commandではない。

- holdout: `search` / `generate` / `verify` / `generate-v2-candidate`  
  `orchestrator/campaign/s8b_holdout_freeze.py:1864-1919`
- oracle: `gate-check` / `run-block`  
  `orchestrator/campaign/s8b_oracle_driver.py:1829-1894`
- p3 pilot CLI: `p3_autonomous_workload_trial`  
  `orchestrator/campaign/p3_autonomous_workload_trial.py:4690-4828`

p3のformal profileは事前検証で拒否されるため、上記CLIをformal submission commandと呼ばない。`docs/phase3-s8c-autonomous-trial-runbook.md:61-72`

### (h) 停止条件

正本の停止条件は以下。

- 各cellは厳密に`G=2`、性能早期停止なし。`docs/phase3-8c-preregistration.md:91-95,497-519`
- crash後はfreeze-wide事前割当attempt registryの範囲内だけ再走可能。`docs/phase3-8b-descriptor-design.md:518-543`
- oracleは全schedule行がterminalにならなければ`protocol_violation`。`orchestrator/campaign/s8b_oracle_driver.py:1783-1803`
- oracle CLIのexit codeは `completed=0`、`refused/budget=2`、`protocol_violation=3`、internal error=1。`orchestrator/campaign/s8b_oracle_driver.py:1852-1871`

現行p3は正式停止条件と一致しない。

- `MAX_APPROVED_GENERATIONS=2` は上限であり、厳密な下限ではない。`orchestrator/campaign/p3_autonomous_workload_trial.py:134-139`
- CLI既定値は1。`orchestrator/campaign/p3_autonomous_workload_trial.py:4694-4708`
- supervisor wall budgetで次generationを開始せず停止できる。`orchestrator/campaign/p3_autonomous_workload_trial.py:3491-3508`
- harnessの `stop_reason != continue` でも途中停止する。`orchestrator/campaign/p3_autonomous_workload_trial.py:3817-3819`
- wall budgetはbench実時間budgetの代替ではない。`docs/phase3-s8c-autonomous-trial-runbook.md:221-225`

なお、`phase3.md` の古い「上限1」は現行D410・runbook・コードの上限2と食い違うため、段3でepochを確定する必要がある。

`docs/phase3.md:490-498`  
`docs/decisions.md:17149-17190`  
`docs/phase3-s8c-autonomous-trial-runbook.md:120-128`

## 4. briefに追加すべき一次資料

- `docs/phase3-8b-restart-runbook.md:3-7,48-64,163-190,258-275`  
  scope-B、oracle gate拒否、v2 producer不在を直接記載。
- `docs/phase3-s8c-autonomous-trial-runbook.md:61-72,160-196,221-225,286-288`  
  H1/H2拒否、artifact layout、file-drawer、正式系列の形を記載。
- `docs/phase3-8c-wiring-design.md:10-29,260-320,398-451,572-585`  
  design-only、formal consumer条件、launch capability、現状0/3を記載。
- `docs/phase3.md:19-37,462-529`  
  8cはoperational pilotで、正式H1/H2・crash resume・bench-time budgetが未完であることを記載。
- `docs/decisions.md:7048-7071` — D145。floor infraの前提4件。
- `docs/decisions.md:12507-12530,18175-18186,22358-22366` — D272/D437/D547。calibration・freeze世代交代・human lockstep。
- `docs/decisions.md:20786-20834` — D501。median-of-medians、trial数未凍結、D496との実装残差。
- `docs/decisions.md:20988-21039` — D505/D506。arm authorityとoff中立入力。
- `docs/decisions.md:21225-21260` — D510。paired差分、attempt registry、非干渉性、仕様のみ発効。
- `docs/decisions.md:21856-21980,22054-22110` — D529、D533〜D539。評価器の段階登録、C07、floor artifact、cell集合の扱い。
- `docs/decisions.md:22604-22622` — D555。現用judgeが旧条件3/scale gateを使うという別系統の残差。
- `docs/decisions.md:23453-23482` — D581。floor測定のprovenance標準変更。
- `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g10.json:1`  
  brief・prereg本文のg8/v4記述とのepoch不一致。

## 5. blocker table 草案

| 項目 | 現状 | 根拠 file:line | 次の一手 |
|---|---|---|---|
| §5記入欄 | 9項目中8項目が未記入 | `docs/phase3-8c-preregistration.md:185-197` | human owner、env、seed、manifest、paired parametersを確定。ただしjudge実装後。 |
| §6充足判定 | 7評価器はdispatch対象だが、充足返却経路は0。5条件は対象外 | `docs/phase3-8c-preregistration.md:303-317,328-337` | active condition-freeze epochを確定し、SATISFIED経路の有無を再監査。 |
| H1/H2正式admission | 定義・digest足場はあるがformal profileが明示拒否 | `p3_autonomous_workload_trial.py:235-242,817-896` | CLIからeffective preregまでを段3で追跡。 |
| on/off/swapped非干渉性 | arm bindingはあるがC02充足証明はない | `docs/phase3-8c-preregistration.md:96-109,204-212` | 7 sink全ての実bytesとholdout間byte同一性を検査。 |
| 6-cell manifest | prereg上は必須だが、`schedule.v1.json`は不在 | `docs/phase3-8c-preregistration.md:213-217,502-514` | manifest、schedule、registry pathの権威を確定。 |
| exact G=2 | 規範はG=2、現行CLI既定は1、実行中の途中停止も可能 | `docs/phase3-8c-preregistration.md:91-95`; `p3_autonomous_workload_trial.py:3491-3508,3817-3819` | exact lower-bound consumerの有無を確認。 |
| crash/attempt registry | 8bはfreeze-wide registryを要求、p3 supervisorは別state machine | `docs/phase3-8c-preregistration.md:82-87,218-225`; `docs/phase3-8b-descriptor-design.md:518-543` | formal registryとの実行経路一致を確認。 |
| paired judge | `n/delta_min/sd_max`未記入、現行supervisorは成功判定を計算しない | `docs/phase3-8c-preregistration.md:189-197,231-239` | judge・3表・validatorのproduction到達性を確認。 |
| floor/v2 freeze | v1 freezeは存在するがfloor/budget null、v2 candidate/approval不在 | `output/s8b-freeze/holdout_freeze.json:620-624`; `docs/phase3-8b-restart-runbook.md:258-275` | D581のT-425適用範囲、v2 path authorityをhuman裁定へ返す。 |
| oracle実走 | gateはfloor-null/budget-null、manifest必須 | `docs/phase3-8b-restart-runbook.md:138-142`; `s8b_oracle_driver.py:1837-1848` | v2 ratified freeze、manifest、calibration、budgetを別々に閉じる。 |
| rr80/rr20 calibration | H1/H2 calibration未登録 | `output/insights/2026-08-20_t425-dependency-reaudit/README.md:22-26,38-61` | calibration登録とg2 activationのhuman lockstep。 |
| T-424/T-272 / D145 | 部分実装だがjob-result binding等が未閉包 | `output/insights/2026-08-20_t425-dependency-reaudit/README.md:63-91` | 全閉包かD145決定5再訪のどちらかを人間裁定。 |
| scope-B/Q3 | 手順は正本化済み、T-139稼働状態は別途確認要 | `docs/phase3-8b-restart-runbook.md:19-28` | qstat・scope-B land・T-139状態を別監査。 |
| human oracle authority | staged diff review以上は機械強制不可 | `docs/decisions.md:15565-15587` | 「機械承認」と書かず、人間review receiptの範囲だけ記録。 |

## 総括

(P2) は、§5の8未記入、充足返却経路0、§7の明示、formal profile拒否により支持される。  
ただしH1/H2定義・arm実装足場は存在し、「実装なし」ではなく「正式admission未成立」と表現する。  
T-425、calibration、v2 freeze、paired judge、attempt registry、exact G=2が主要blockerである。  
briefのv4 epoch、v2 artifact path、P3のListAgents状態は段3で再確認する。