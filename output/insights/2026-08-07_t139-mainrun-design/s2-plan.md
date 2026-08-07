## 総括

実験計画の起草は可能だが、現時点の本走投入は **NO-GO** である。理由は次の4点。

- allocation 間分散は J=1 の probe から推定不能であり、J≈11を固定できない。[package.md:149–151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-03_t338-rf-statistical-design/package.md:149)
- probe の「5 rep balanced schedule」は厳密 balance ではない。全6順列から `mode1 stock modeX` を除いた5順列で、位置・一次 carry-over の各頻度は1または2である。[order.tsv:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/order.tsv:2)
- `δ_D` の数値を正当化する候補非依存の根拠がrepo内にない。probe値から選ぶ P4 は、未較正データを見た後の outcome-informed 設計になる。
- D162機械化は0/9層で、特に trusted consumer が0件である。[mechanization-design.md:3–7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-05_t337-qualification-authority/mechanization-design.md:3)

推奨する二段階案は、**external pilot Jp=8、pilot非pool、cluster内6 rep、本走Jはpilot後の事前固定式で決定**である。d=1.0の正規近似 J=11 は sanity lower bound にすぎず、本走値として固定しない。

## 親 provisional 裁定への判定

| 項目 | 判定 | 根拠 |
|---|---|---|
| P1 external pilot・非pool | **採用** | D116/8cにinternal pilot poolingの前例は見つからない。D116はgit ancestryと双射の規定であって標本再利用の許可ではない。[D116:5494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/docs/decisions.md:5494) |
| P2 5 rep据置き | **そのままでは棄却** | 実 schedule は近似balanceであり、厳密な位置・一次carry-over balanceには6順列が必要。5 repを採るならbalanceはcluster横断で行い、Jを6の倍数へ丸める別設計になる。 |
| P3 `N>0 ∧ D>δ_D`だけ | **棄却** | partial recoveryには `G=stock−X>0` も必須。D162も `D>δ_D ∧ N>0 ∧ G>0` を要求する。[D162:8018–8025](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/docs/decisions.md:8018) |
| P4 probe劣化幅から `δ_D` | **棄却** | probeはJ=1・未較正で、レコード数をcalibration/floor入力にしないと明記する。[README.md:143–151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-05_t139-alt-x-probe/README.md:143) |
| P5 d=1、J≈11固定 | **d=1だけ維持、J固定は棄却** | J=11はα=.05/6・component power 80%の正規近似。本来のglobal conjunction powerとpilot covarianceを反映していない。 |
| P6 producerだけ先行 | **本走について棄却** | validatorが要求するraw fieldを後決めすると、欠落事実は復元不能でJ allocation全部を捨てる。consumerは同一呼出し内でvalidatorを再実行しなければならない。[D162:8022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/docs/decisions.md:8022) |

internal pilotをnaiveにpoolしてはいけない反例も閉形式で書ける。帰無下で `Z1,Z2~N(0,1)`、`Z1>0`ならpilotで停止、`Z1≤0`なら同数を追加して `(Z1+Z2)/√2` を通常の5%片側臨界値で検定する規則では、

\[
P_0(\mathrm{reject})
=.05+\int_{-\infty}^{0}\phi(z)
  [1-\Phi(\sqrt2 z_{.95}-z)]\,dz
=.05125>.05.
\]

本件はeffect sizeもpilotから読むため、非pool external pilotが最も明快である。

## studyの段階と着手順

### 0. 裁定・正本整合

本走前に以下を閉じる。

1. 下記「ユーザー裁定へ返す項目」を確定する。
2. paired RFをD19の限定例外としてroadmap §3.6へ原子的に記録する。現行roadmapは「variantとbaselineは決して同一sessionで測らない」と書いたままである。[roadmap.md:219–225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/docs/roadmap.md:219)  
   D134はこの限定を同じ変更単位で行うよう要求している。[D134:6506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/docs/decisions.md:6506)
3. W1/W2の正式record数をPegasusで較正する。probeのW1=10k、W2=100kは未較正なので流用しない。
4. exact modeX bytes、workload、environment、candidate系列IDを固定する。

### 1. 9層のvertical slice

将来の実装waveでは、少なくとも次を本走前にE2E化する。

| 層 | 将来の配置案 | 必須内容 |
|---|---|---|
| 1 計測producer | `[new] tools/pegasus/rf_positive_control.{pbs,sh}` | probeのwalltime/deadline契約を継承するが、probe本体は変更しない。[probe.pbs:1–5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/tools/pegasus/probes/t139_positive_control_probe.pbs:1) |
| 2 attempt registry | `[new] orchestrator/qualification/rf_attempt_registry.py` | 全submission、失敗、置換、未使用reserveをappend-onlyに記録 |
| 3 schedule validator | `[new] .../rf_schedule.py` | planned/actual schedule、位置、carry-over、washout timestampのexact照合 |
| 4 RF calculator | `[new] .../rf_statistics.py` | cluster summary、同時領域、Holm、Fieller、境界閉表 |
| 5 適格性validator | `[new] .../rf_validator.py` | raw pathから単一snapshotを再読し全件再計算 |
| 6 Layer 3次版 | `orchestrator/campaign/layer3_*` | RF区画を既存floor表と分離。現行はsource-ref双射のみ。[layer3_report.py:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/orchestrator/campaign/layer3_report.py:178) |
| 7 selector consumer | `[new] RF admission hook` | decisionを入力せずraw pathからvalidatorを再実行 |
| 8 材料レポートconsumer | 同上 | cell/Fieller/attempt全件を投影 |
| 9 双射・変異検査 | `[new] test_rf_qualification_*` | 自己申告、schedule欠落、失敗trial脱落、validator偽装をkill |

raw receipt schemaは `[new] orchestrator/qualification/rf_raw_receipt_schema.json` とし、次を含める。

- `declared_use_class`（`artifact_role`は禁止）
- `rf_trial_id / parent_family_id / candidate_id`
- preregistration path・commit・hash、measurement checkout
- allocation ID、node、時刻、accounting、env tag、pin、attestation
- 三armのsource/binary/compile identity
- planned scheduleとactual schedule
- 各runのworkload・arm・rep・position・previous arm・timestamp・raw TPS
- correctness、liveness、admission telemetry
- 全attempt、reason code、replacement relation

`eligibility_status`、`pairing_valid`、`rf_acceptance_status`、validator identity/result等は未知fieldとして拒否する。これはD162決定(2)の直接適用である。[D162:8014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/docs/decisions.md:8014)

### 2. external pilot

推奨値は以下。

- `Jp=8 complete allocations`
- reserve 2本、事前順序固定
- cluster内6 rep
- pilot rawは本走の推定・p値・Fiellerへ一切poolしない
- pilot preregistrationには、後述のJ算出式・simulation seed・候補J範囲・J上限を先に書く

pilotが推定するものは次である。

1. allocation間の三arm cluster summaryの共分散
2. `N`、`D−κS`、`G` の各効果と相関
3. cluster内rep残差・位置・一次carry-over
4. washout後のnode telemetry回復
5. allocation実時間、infra failure率
6. request単位point消費

Jp=8なら正規近似でSD推定の相対SEは約27%なので、pilot推定を真値扱いせず上側分散限界を使う。

### 3. J算出と本走事前登録

arm代表値は、推奨として各allocation内6 repの中央値（偶数なので中央2値の平均）とする。

\[
\begin{aligned}
N_{wj}&=m_{X,wj}-m_{Dg,wj},\\
D_{wj}&=m_{S,wj}-m_{Dg,wj},\\
G_{wj}&=m_{S,wj}-m_{X,wj}.
\end{aligned}
\]

`δ_D` はstock比 `κ_w` なので、分母条件をplug-in thresholdにせず

\[
E[D_{wj}-\kappa_w m_{S,wj}]>0
\]

という線形contrastとして同時領域へ入れる。

pilotの各primary component \(k\) について、事前固定したplanning confidence \(\gamma\) を用い、

\[
\sigma^+_k
=s_{p,k}\sqrt{\frac{J_p-1}{\chi^2_{\gamma,J_p-1}}},
\quad
\Delta^-_k
=\bar\Delta_{p,k}
-t_{1-\gamma,J_p-1}\frac{s_{p,k}}{\sqrt{J_p}},
\]

\[
d_{\rm plan}
=\min\left(1.0,\min_k\frac{\Delta^-_k}{\sigma^+_k}\right)
\]

とする。`d_plan≤0`なら本走を投入しない。

次に、pilot共分散、actual acceptance predicate、restricted schedule、weak-null較正を使う固定simulationで、

\[
J_{\rm main}
=\min\{j:
LCB_{99\%}(\widehat{\Pr}[A_j=1])\ge0.80\}
\]

を選ぶ。推奨設定はsimulation \(B=10^6\)、seedはpilot preregistration commitから決定、探索範囲は `11..J_max`。該当Jが無ければ `design_not_feasible` で停止する。main開始後の追加は一切しない。

d=1の簡易確認では、

\[
\left(z_{1-.05/6}+z_{.8}\right)^2 \simeq10.47
\]

なのでJ=11となる。しかしこれはcomponent power 80%である。6 componentのglobal power 80%をunion boundで守るだけでも、

\[
\left(z_{.95}+z_{1-.2/6}\right)^2\simeq12.1
\]

でJ=13相当となる。したがってP5のJ=11固定は不可である。

既存のwithin-cluster RF sdは、W1 `0.00575`、W2 `0.00366`だが、primaryのallocation間分散ではない。平均RFのcluster内SEはそれぞれ約 `0.00257 / 0.00164`にすぎない。

rep数の感度は、平均型のrandom-intercept近似

\[
Var(\bar Y_j)=\sigma_B^2+\sigma_W^2/r
\]

で確認できる。\(k=\sigma_B/\sigma_W\) とすると、

\[
\frac{J(r')}{J(r)}
\simeq\frac{k^2+1/r'}{k^2+1/r}.
\]

J=11を前提に5→6 repでJを10以下へ落とせるのは `k≤0.408`、すなわちRF単位ではW1 `σ_B≤0.00235`、W2 `≤0.00149`のときだけである。5→10なら `k≤0.949`。実際のcluster間 `k` は不明なのでpilotより前には決められない。

なおP5の「W1 N=93,373、within sd=4,009」は量を混同している。4,009はmodeX arm単体のsdであり、rawから求めたpaired `N=modeX−mode1` のsdは約5,175である。[throughput.tsv:2–16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/throughput.tsv:2)

## primary claimと受理署名

### family

Q7の三分割をそのまま使う。

1. **primary:** 「両workloadでpartial recovery」のglobal IUT 1本。
2. **個別公表:** workload × `D/N/G` の6 cellをHolmでstrong FWER制御。
3. **候補系列:** `parent_family_id`、candidate上限、累積alpha、spending ruleを最初の正式trial前に固定。新trial IDでalphaをリセットしない。

BHは使わない。[package.md:216–223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-03_t338-rf-statistical-design/package.md:216)

### 判定述語

各workload \(w\) のQ3同時信頼領域を \(C_w\) とする。

\[
\begin{aligned}
P_w \equiv&
\inf_{C_w}N_w>0\\
&\land \inf_{C_w}(D_w-\kappa_wS_w)>0\\
&\land \inf_{C_w}G_w>0.
\end{aligned}
\]

Fieller集合を \(F_w\) とし、最終受理は

```text
rf_positive_artifact :=
  raw_schema_valid
  AND exact_J_complete
  AND all_attempts_bijective
  AND no_correctness_anomaly
  AND schedule_and_washout_valid
  AND pairing_valid
  AND candidate_series_alpha_valid
  AND P_W1
  AND P_W2
  AND fieller_ok_W1
  AND fieller_ok_W2
```

```text
fieller_ok_w :=
  shape == bounded_single_interval
  AND lower > 0
  AND upper < 1
```

`G>0`とFieller `(0,1)` は数学的には同じ方向を表すが、validatorは両方を再計算し、不一致を `statistical_inconsistency` として拒否する。P3のようにGとFiellerを外すと、stock超過候補まで正例にできる。

### Fieller

cluster-level sample mean/covarianceから

\[
F_w=\left\{r:
(\bar N-r\bar D)^2
\le\frac{q_w^2}{J}
(s_{NN}-2rs_{ND}+r^2s_{DD})
\right\}
\]

を常に出す。分母screening後だけ報告する形にはしない。[package.md:248–268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-03_t338-rf-statistical-design/package.md:248)

係数

\[
A=\bar D^2-q^2s_{DD}/J,\quad
B=\bar N\bar D-q^2s_{ND}/J,\quad
C=\bar N^2-q^2s_{NN}/J
\]

に対し、`Ar²−2Br+C≤0`を解く。`A>0`ならbounded、`A<0`なら通常disjoint、`A=0`や全実数はunboundedとして表す。

境界閉表は、非空の閉集合Fについて各境界 `b∈{0,1}` との関係を

```text
below | contains | above | split_without_containing
```

のexact-oneで持たせる。

| Fieller shape / 位置 | 状態 | 正例受理 |
|---|---|---:|
| bounded、全体が0未満 | `below_degraded` | false |
| bounded、全体が `(0,1)` | `partial_recovery` | true候補 |
| bounded、全体が1超 | `stock_exceeding_unattributed` | false |
| bounded、0または1を含む・等しい | `boundary_ambiguous` | false |
| unbounded connected / all-real | `unbounded_not_certifiable` | false |
| disjoint | `disjoint_not_certifiable` | false |
| empty・表現不整合 | `invalid_confidence_set` | false |

弱い分母は固定状態名 `weak_denominator_not_certifiable` とする。`RF>1` はstock超過とだけ記録し、recoveryや新規改善へ帰属しない。[D162:8031–8033](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/docs/decisions.md:8031)

### 合否例

通る合成例：

```text
W1: LCB(N/S)=0.10, LCB(D/S-κ)=0.20, LCB(G/S)=0.60,
    Fieller=[0.12, 0.18]
W2: LCB(N/S)=0.11, LCB(D/S-κ)=0.18, LCB(G/S)=0.58,
    Fieller=[0.13, 0.17]
全raw/attempt/schedule/correctness/alpha条件成立
```

両workloadのFiellerがboundedかつ `(0,1)` 内なので受理。

落ちる合成例：

```text
W1: pass
W2: LCB(N)>0, LCB(D/S-κ)>0 だが LCB(G/S)=-0.01,
    Fieller=[0.82, 1.04]
```

W2が1を含むため `boundary_ambiguous`、global IUTはfalse。P3の二条件だけなら誤って通る負例である。

## `δ_D` の決め方

\[
\delta_{D,w}=\kappa_w E[S_w]
\]

ではなく、同じデータでplug-inした絶対TPSを閾値にせず、主検定を `E[D−κ_wS]>0` とする。

probe実測の `D/stock` はW1約88.2%、W2約90.2%だが、これを見て「十分小さいκ」を選ぶ根拠にはできない。さらにprobe事前登録は、pass後にexact bytesを後続RF studyへ送ることしか規定しておらず、probe値からκを導く規則を置いていない。[preregistration.md:124–130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/preregistration.md:124)

判定は次のとおり。

- 完了済みprobeの受理条件を書き換えるわけではないため、D126決定(4)への文字通りの違反ではない。
- ただしmainの閾値を選択済みcandidateの未較正結果から決めるので、**候補非依存のconfirmatory thresholdではない**。
- 使うなら「probe-informed design」と開示し、mainを完全な独立確認と呼ばない。
- 推奨は、workloadごとの実用最小劣化率 `κ_W1 / κ_W2` をユーザーがcandidate結果と独立に定めること。現repoから数値は導けず、現状は不明である。

## schedule、carry-over、washout

### probeが実際にしていたこと

probeは両workloadで同じ5順列を固定していた。[preregistration.md:53–62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/preregistration.md:53)

- 全6 arm順列のうち `mode1 stock modeX` だけが無い。
- position頻度:
  - stock `(2,1,2)`
  - mode1 `(1,2,2)`
  - modeX `(2,2,1)`
- block内一次carry-over:
  - `S→D, D→X, X→S, X→D` は2回
  - `S→X, D→S` は1回
- W1を常にW2より先に実行。
- 実装上、arm間の明示的washoutは無い。[probe.sh:493–523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/tools/pegasus/probes/t139_positive_control_probe.sh:493)

したがって「balanced」は差1以内という意味で、exact balanceではない。

### 推奨main schedule

cluster内6 repとし、三armの全6順列を各1回使う。

```text
S D X
S X D
D S X
D X S
X S D
X D S
```

- 各armは各positionにexactly 2回。
- 6種類の有向carry-overはexactly 2回。
- 6 blockの実行順は `6!` の許容集合から事前seedで選ぶ。
- W1/W2のblock順はcluster間で差1以内にcounterbalance。
- schedule/seed/hashをmain preregistration commitへ固定し、runtime乱数を使わない。
- sharp nullは副次感度分析、**weak mean nullをprimary**とする。estimandが平均contrastだからである。
- weak-nullの型I誤りは、同じ許容schedule集合を使う事前simulationで較正する。

washoutの推奨原案は以下。

- 各arm process終了後、最低30秒待つ。
- 各3-arm block間およびworkload切替時は最低60秒。
- 最後の5秒間に、事前登録したload/clock/admission telemetryがpre-run envelope内へ5回連続で戻ること。
- 60秒で戻らなければ、最初のperformance run前ならclosed infra failure、開始後なら `post_performance_environment_failure` として判定不能。開始後の置換は禁止。
- exact秒数とtelemetry fieldは本走前のユーザー裁定対象。現データは30/60秒の十分性を実証していない。

現probeのworst-case timeout予算は3290秒/内部3300秒で余白10秒しかないため、6 repとwashoutを単純追加してはならない。新driverは全cap総和を3300秒以下へ再配分し、pilotで成立を確認する。

## schema変更による再走risk

riskは **高**。現在0/9層なので、producer単独でmain rawを取る案は採らない。

- 後から追加できるのは、既存rawから再計算できる派生fieldだけ。
- allocation accounting、actual schedule、arm binary identity、correctness、全attempt、washout timestamp等がrawに無ければ復元不能。
- 復元不能fieldがvalidator必須になれば、mainのJ allocation全部を再走する。
- J=11なら最大11時間のrequested allocation、内部予算36,300秒を失う。point損失は未実測なので算定不能。
- schemaはexternal pilot後・main前にversion固定する。main中のschema変更は新trial扱いにし、旧rawを黙って昇格させない。

D162決定(10)はconsumer実hookを機械化発火条件に含める一方、現在consumerは0件である。[D162:8049–8055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/docs/decisions.md:8049)  
したがって「producerだけ先行」も「consumer不在のまま9層を実装」もそのままでは通らない。後述のとおり、既存positive probeを根拠に9層vertical sliceを原子的に許すか、consumer-firstを要求するかを裁定へ返す。

## 資源見積り

既知値:

- 1 cluster = 1 gen_S allocation
- requested walltime = 3600秒
- 内部deadline = 3300秒
- SFC残 = `5236.04 / 6000`
- 消費済み = `763.96`、残率約87.27%
- gen_S request = 104件中31 running（約29.8%）
- 1 allocation当たりpoint消費 = **不明**

推奨案 `pilot 8 + pilot reserve 2 + main J=11 + main reserve ceil(0.2J)=3` の例では、

| 区分 | allocation数 | requested | 内部上限 |
|---|---:|---:|---:|
| pilot本体 | 8 | 8時間 | 7時間20分 |
| pilot reserve | 2 | 2時間 | 1時間50分 |
| main本体（仮にJ=11） | 11 | 11時間 | 10時間5分 |
| main reserve | 3 | 3時間 | 2時間45分 |
| 合計 | 24 | 24 allocation-hours | 22 allocation-hours |

正式には、

\[
A_{\max}=J_p+R_p+J_{\rm main}+R_{\rm main}+A_{\rm calibration},
\qquad
Points_{\max}=A_{\max}p_{\rm alloc}.
\]

`p_alloc`もcalibration allocation数も不明なので、現在の5236.04から「何cluster走れる」とは言えない。account全体の`rbudgetcheck`差分は、104 requestが併存するためT-139一件のpoint消費と帰属できない。最初のpilot 1〜2本でrequest単位のscheduler accountingを取得し、pointが確定するまで残りをbulk submitしない。

reserveは、性能開始前のclosed infra failureにだけ順序どおり使用する。correctness anomalyは終端reject、性能開始後の失敗はrejectまたは判定不能で、reserve置換しない。[package.md:227–243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-03_t338-rf-statistical-design/package.md:227)

## ユーザー裁定へ返すべき項目

1. **`κ_W1 / κ_W2` の数値または候補非依存の導出規則**  
   受理集合を直接変える。probe値からの導出は推奨しない。

2. **D162発火条件の解決方法**  
   推奨はD187のpositive probeを発火根拠に、producer・validator・最初の材料レポートconsumer・双射検査を原子的なvertical sliceとして許可する案。正しさ権威境界に触るため親独断不可。

3. **pilotサイズとpool禁止**  
   推奨はexternal `Jp=8`、非pool、reserve 2。Jp=16ならSD推定は約18%まで改善するが費用が倍になる。

4. **cluster内rep設計**  
   推奨は6 rep exact balance。5 rep案を残すなら、6種類の「1順列欠落」scheduleをcluster間で均等化し、Jを6の倍数へ丸める必要がある。費用と受理集合が変わる。

5. **washoutの数値とfailure分類**  
   推奨原案30秒/60秒。carry-over防壁とwalltime双方に触る。

6. **J planning assurance、`J_max`、global power目標**  
   d=1は裁定済みだが、component 80%かglobal conjunction 80%かでJが変わる。推奨はglobal 80%、simulation powerの99%下限で決め、`J>J_max`なら投入しない。

7. **候補系列のalpha spendingとcandidate上限**  
   cap=1でmodeXへα=.05を全投入するか、将来候補用に分割するか。同じresearch familyでtrial IDだけ変えてalphaをリセットできない。

8. **reserve数とstudy point上限**  
   推奨は `ceil(0.2J)` だが、point単価の実測後に承認が必要。

9. **arm代表値**  
   packageは`m=arm代表値`までで、中央値か平均かを閉じていない。推奨は6 rep中央値。変更するとRF、Fieller、Jが変わる。

10. **最初のtrusted consumer**  
    材料レポートを先にするかselectorまで同時に結線するか。D162の発火条件と9層完了範囲を変える。

本回答は静的検査のみで、pytest・build・benchmark・Pegasus実走は行っていない。