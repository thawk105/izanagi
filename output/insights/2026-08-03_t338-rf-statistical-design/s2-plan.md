# RF 統計設計 5 点 — ユーザー裁定パッケージ案

## 共通の推定対象

現行の provisional 定義は \(RF=(S_X-S_D)/(S_S-S_D)\) だが、`S` の集約方法が未確定である `output/insights/2026-07-29_t139-silo-degradation-ladder-design.md:169`。以下を 5 点共通の前提として追加裁定する必要がある。

- \(m_{a,w,j}\): arm \(a\in\{S=\mathrm{stock},D=\mathrm{degraded},X=\mathrm{candidate}\}\)、workload \(w\)、独立 session \(j\) における、事前固定した 5 rep の中央値。
- \(N_{w,j}=m_{X,w,j}-m_{D,w,j}\)、\(D_{w,j}=m_{S,w,j}-m_{D,w,j}\)、\(G_{w,j}=m_{S,w,j}-m_{X,w,j}\)。
- 推定対象は、事前登録した session 母集団に対する
  \[
  RF_w=\frac{E[N_{w,j}]}{E[D_{w,j}]},
  \qquad
  \widehat{RF}_w=\frac{\bar N_w}{\bar D_w}.
  \]
  すなわち「session median の平均の比」とし、「arm ごとの median-of-medians の比」にはしない。
- primary endpoint は trace-disabled の `throughput_tps` 一つ。abort 率等は説明用の副次 endpoint とし、RF familyへ後付けしない。

現在の probe の `rep` は 1 allocation 内の反復であり、独立 session ではない。実データには `workload / arm / rep / throughput_tps` はあるが session 軸がない `output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/throughput.tsv:1`。この区別を凍結しない限り、5 点を裁定しても推定量が一意にならない。

## ① paired block の帰無分布

### 問いの厳密な言い直し

各 workload について、少なくとも次の片側帰無仮説を、何を交換可能単位として、どの有限標本分布で検定するかが未決定である。

- 分母識別: \(H^{D}_{0,w}:E[D_{w,j}]\le\delta_{D,w}\)。
- recovery: \(H^{N}_{0,w}:E[N_{w,j}]\le0\)。
- partial recovery を主張する場合: \(H^{G}_{0,w}:E[G_{w,j}]\le0\)。

ここで \(\delta_D\) は点③で決める事前登録済みの最小識別幅である。session が独立標本単位であり、session 内 rep は標本数を増やさない。

### 択一

A. 実際の割付を再現する restricted randomization test

各 session 内で arm を測定位置へ無作為割付し、帰無分布も同じ割付制約を再現する。統計量は session-level contrast の studentized mean とする。Fisher の sharp null に対して有限標本で exact、平均効果の weak null に対しては studentization と十分な session 数を要する。最大の犠牲は、schedule receipt、位置 balance、carry-over 防止がすべて必要になることである。

B. paired \(t\) 検定

\(d_j\) が独立で、おおむね正規または session 数が十分であると仮定する。平均差という推定対象には直結し、検出力も比較的高いが、8 session では外れ値・歪度を診断できず、正規近似への依存が強い。

C. sign test / Wilcoxon signed-rank

sign test は差の中央値、Wilcoxon は対称分布下の位置差を対象とする。分布仮定は弱まるが、共通推定対象である平均差からずれ、8 session では p 値が極端に離散化する。

### 推奨

A を採る。ただし P2 の「session を交換単位とする」は厳密には修正が必要である。session index を並べ替えても paired contrast は変わらない。固定するのは session であり、交換するのはその session 内の測定位置へ無作為に割り付けた arm label である。

実 schedule は各 rep の arm 順を持っている `output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/order.tsv:1` が、独立 session、無作為化 algorithm、seed の field はない。一方、既存 rung artifact には algorithm と seed を持つ `schedule_receipt` の先例がある `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:3849`、`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:3998`。D104 も同一 allocation 内の A-B/B-A と機構発火の直接観測を要求している `docs/decisions.md:4658`、`docs/decisions.md:4661`。

### 成果物影響

帰無分布を誤ると adjusted p 値と各 workload の pass が変わり、同じ raw 値から正例 artifact、certified 選択、材料レポート、proof chain の受理可否が反転する。

### 入力 field の実在

既存するのは `order.tsv` の `workload / rep / position / arm` と、`throughput.tsv` の `throughput_tps` だけである。producer 側の新出力要件は次である。

- `rf_sessions[].rf_session_index`
- `allocation_receipt_ref`、`node_identity`、`env_tag`
- `randomization.algorithm`、`randomization.seed`、`schedule_sha256`
- `runs[].workload_id / rf_arm_role / arm_artifact_id / rep_index / position / throughput_tps`
- schedule と実走順の exact match 判定

既存の `rep` を独立 session の意味へ変更してはならない。`variant` も binary identity として既に使われているため、`rf_arm_role` と二分する。

## ② 多重比較 family

### 問いの厳密な言い直し

1 本の正例 artifact が複数 workload・複数 contrast・場合によっては複数 candidate を調べるとき、どの帰無仮説集合について

\[
P(\text{少なくとも一つの偽の確証を受理})\le0.05
\]

を保証するかが未決定である。「primary metric が一つ」であることだけでは、workload、contrast、candidate の多重性は消えない。

1 candidate・2 workload で partial recovery \(0<RF<1\) を主張するなら、基本 family は

\[
\mathcal F=
\{H^D_{0,w},H^N_{0,w},H^G_{0,w}:w\in W\}
\]

の 6 仮説である。結果を見た後に candidate を差し替える場合は、その candidate 軸も family または事前登録した alpha-spending に含める。

### 択一

A. Holm による strong FWER 制御

任意の依存構造で有効で、family が小さければ監査しやすい。犠牲は、paired 相関を利用しないため保守的になること。

B. joint randomization maxT

全 contrast の最大統計量を同じ block randomization から作り、依存を利用して strong FWER を制御する。Holm より高い検出力を期待できるが、全 cell の complete block と joint schedule が必要で、欠測時の設計が複雑になる。

C. intersection-union test

公表する主張を「全 workload・全 contrast が同時に成立」の一つだけに限定し、各 component を \(\alpha\) で検定する。global `all_pass` だけなら無補正でも型 I 誤りを制御できるが、workload 別の確証や材料レポート上の個別主張はできない。

### 推奨

A の Holm、family-wise \(\alpha=0.05\) を採る。材料レポートと proof chain は cell 別判断を保持するため、C の「global claim だけ」という制約と合わない。BH/FDR は発見集合中の偽陽性割合を管理する手続きであり、単一 certified artifact の偽受理確率には適さないという P3 の判断に賛成する。

ただし P3 の family は狭すぎる。全 `workload × contrast` に加えて、同じ正式系列で試す全 candidate と、結果により acceptance を変える全 endpoint を、実走前に閉表化する必要がある。D126 は結果後の candidate 差し替えと workload 縮小を明示的に拒否している `docs/decisions.md:6216`、`docs/decisions.md:6219`。

### 成果物影響

family の境界を狭くすると adjusted cutoff が緩み、正例 `all_pass` と certified 選択が増える一方、材料レポートと proof chain の FWER 主張が成立しなくなる。

### 入力 field の実在

既存 probe には `workload` と `arm` はあるが、primary endpoint、hypothesis ID、candidate universe、family ID、alpha はない。新出力要件は次である。

- preregistration 側: `primary_endpoint`、`hypotheses[]`、`family_id`、`family_members[]`、`alpha`、`adjustment="holm"`
- artifact 側: `hypothesis_id / raw_p / adjusted_p / reject / direction`
- `candidate_trial_id` と事前登録された全 candidate manifest
- 全 attempt と全欠落 trial の registry

既存 root の `all_pass` は RF 用に再利用しない。既存 rung は `all_pass=true` でも `recovery_measurement_eligibility=false` である `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:8`、`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:136`。新名は `rf_acceptance_status` とする。

## ③ between-run floor の種類

### 問いの厳密な言い直し

RF の差に対する測定誤差を、arm ごとの周辺分散、paired contrast の分散、またはモデル化した分散のどれで表すか。また「1 session の差の散布」と「平均差を判定する confidence margin」を同じ floor と呼ぶかが未決定である。

現行 `between_run_noise_floor()` は単一 baseline arm の session median の CV である `orchestrator/calibrator/stability.py:102`、`orchestrator/calibrator/stability.py:128`。実 JSON も `genome` は一つで、`between_run.session_throughputs` しか持たない `output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json:7`、`output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json:40`。これは RF の paired difference floor ではないというレンズ B の指摘は正しい `output/insights/2026-08-02_t139-positive-control-probe/s3-lensB.md:3`、`output/insights/2026-08-02_t139-positive-control-probe/s3-lensB.md:9`。

### 択一

A. contrast 別 paired floor

各 workload・contrast について \(s(d_{c,w,j})\) を保存し、平均差の判定には \(s/\sqrt J\) と point①②の臨界値から作る one-sided confidence margin を使う。session 共通外乱の covariance を正しく相殺できるが、完全な block 対応と独立 session が必須である。

B. unpaired marginal floor

arm を独立に収集し、独立設計なら \(\sqrt{s_a^2+s_b^2}\) を使う。pairing が無い実験にも適用できるが、共通外乱を除けず検出力を失う。paired データを事後的に unpaired と読み替える場合、負の covariance もあり得るため必ずしも保守的ではない。

C. session・arm・時間窓の mixed-effects model

session random effect と arm-specific residual を分ける。欠測や異分散を扱える可能性があるが、モデル仮定・診断・実装が重く、8 session では variance component が安定しない。

### 推奨

A を採る。ただし単一 scalar を `floor` と呼ばず、次の二量を分ける。

- `rf_paired_between_session_sd_tps`: \(s(d_j)\)。物理的な session 間散布。
- `rf_paired_decision_margin_tps`: multiplicity-adjusted lower confidence bound と点推定の差。gate が消費する判定余白。

判定は単なる `gap > s(d)` ではなく、たとえば分母なら \(LCB(\bar D)>\delta_D\) とする。実用上の最小効果 \(\delta_D\) を置くなら、noise と混ぜず別 field・別裁定にする。

現行 same-window CV は write 0.666%、balanced 1.067%、read 0.110% だが、各 artifact 自身が cold-boot・時間ドリフトを含まない下限と記録している `output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json:36`、`output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json:52`。したがって RF session は別 allocation・事前固定した複数時間窓へ分散させる。

P1 の paired 化と別名化には賛成するが、paired 前提が壊れたら同じデータを unpaired 判定へ自動 fallback する案には反対する。その場合は `indeterminate` が fail-closed である。事前登録した独立の unpaired secondary protocol がある場合だけ、非 certification の感度分析として出せる。

現行 `BETWEEN_RUN_CV=0.030` は `compare()` 用の別量として不変にする `orchestrator/campaign/p2_2.py:50`、`orchestrator/campaign/p2_2.py:62`。`compare(noise_cv=...)` へ RF paired margin を渡してはならない `orchestrator/calibrator/stability.py:223`、`orchestrator/calibrator/stability.py:236`。Gate1 の √2 保留も本裁定では変更しない `docs/archive/audit-2026-06-30.md:309`、`docs/archive/audit-2026-06-30.md:311`。

### 成果物影響

floor の種類は分母・各 gap の lower bound を直接変えるため、正例成立、RF の報告可否、certified 選択、材料レポート、proof chain の受理集合を反転させる。

### 入力 field の実在

現在の calibration artifact に arm 軸と arm 間 session 対応はない。producer 側で新たに、各 `rf_session_index × workload_id × rf_arm_role` の raw reps、session median、paired contrast、covariance を出す必要がある。

`noise_cv` は既に unpaired `compare()` の引数なので二義化しない。新規 field は `rf_paired_*` namespace に限定する。

## ④ 区間推定と `RF<0` / `RF>1` の帰属

### 問いの厳密な言い直し

比 \(RF=\mu_N/\mu_D\) の confidence set をどの被覆確率で作るか、分母が 0 に近い場合に bounded interval を捏造しないか、さらに 0 と 1 を跨ぐ不確実性を無視して点推定だけで分類するかが未決定である。

### 択一

A. paired Fieller confidence set

\((N_j,D_j)\) の同一 session covariance を使って比の confidence set を作る。分母が弱いと unbounded または disjoint になること自体が正しい診断である。弱点は session-level mean の近似正規性で、少数 session では幅が大きい。

B. session block bootstrap

session を resample し、その内部の三 arm を一緒に保持する。非線形推定量へ適用しやすいが、8 session の percentile/BCa bootstrap は denominator 近傍で被覆が不安定で、見かけ上 bounded な区間を返し得る。

C. \(N-rD\) の検定反転

各候補値 \(r\) に対して paired randomization test を反転する。設計との整合は高いが、constant-effect または weak-null 近似の扱いを明記する必要があり、計算・説明が複雑になる。

### 推奨

A の Fieller を primary、B または C を事前登録した sensitivity とする。P4 の「bootstrap primary、Fieller sensitivity」には反対する。分母識別が RF の中心問題である以上、分母不確実性により unbounded set を返せる Fieller を主に置く方が fail-closed である。

規則は以下とする。

- 分母の multiplicity-adjusted lower bound が \(\delta_D\) 以下なら `rf_status="undefined_denominator"`。RF の点値・区間は報告せず、\(\bar N,\bar D\) と理由だけを残す。
- clamp はしない。provisional 定義も clamp を禁じている `output/insights/2026-07-29_t139-silo-degradation-ladder-design.md:171`、`output/insights/2026-07-29_t139-silo-degradation-ladder-design.md:174`。
- confidence set 全体が 0 未満なら `below_degraded`。これは相対性能の方向であり、機序の帰属ではない。
- 全体が \((0,1)\) 内なら `partial_recovery`。
- 1 を含むなら `indistinguishable_from_stock_boundary`。
- 全体が 1 を超える場合だけ `stock_exceeding`。`recovery` や `new_improvement` という機序帰属はせず、別の機序証拠と ablation を要求する。
- 点推定だけが 0 未満または 1 超で、区間が境界を跨ぐ場合は分類しない。

### 成果物影響

区間法と境界分類を誤ると、同じ点推定が `partial_recovery`、`stock_exceeding`、`undefined` の間で変わり、材料レポート記述、proof chain の主張、正例受理が変わる。

### 入力 field の実在

`throughput_tps` と arm/workload は既存するが、session-paired \(N_j,D_j\)、covariance、RF 区間は存在しない。新出力要件は次である。

- `rf_estimates[].numerator_mean_tps / denominator_mean_tps`
- `paired_covariance` と `complete_sessions`
- `denominator_lcb_tps / denominator_threshold_tps`
- `rf_confidence_set.type = bounded | unbounded | disjoint`
- `rf_confidence_set.intervals[]`
- `rf_classification` と `attribution_status="unattributed"`

単純な `lower/upper` 二値 schema では Fieller の unbounded/disjoint set を表現できない。

## ⑤ 選択的欠測

### 問いの厳密な言い直し

arm 固有の timeout、crash、低 throughput、verifier failure、外乱などが欠測確率と性能値の双方に関係するとき、どの observation を推定母集団へ残すか、欠測後の retry/置換を許すか、名目 FWER・区間被覆を維持できるかが未決定である。

現行 `between_run_noise_floor()` は `None` session を単に除外する `orchestrator/calibrator/stability.py:118`、`orchestrator/calibrator/stability.py:126`。結果の `sessions` も有効数だけである `orchestrator/calibrator/model.py:180`、`orchestrator/calibrator/model.py:182`。理由を持たないこの挙動は RF certification には使えない。

### 択一

A. closed reason code による complete-block 規則

arm 非依存と機械判定できる infrastructure failure の場合だけ session 全体を無効化し、事前登録した reserve session で置換する。arm 固有の timeout、nonzero、correctness failure は欠測として捨てず substantive failure とする。全 attempt を残す。仮定は、infra reason の分類が outcome-blind に実発火すること。

B. 欠測一件で artifact 全体を判定不能

最も保守的で選択バイアスを生まないが、一時的 scheduler/node 障害でも全計画を失う。

C. MAR モデル、multiple imputation、IPW

観測済み共変量を条件に欠測がランダムと仮定する。効率は上げられるが、arm 固有 crash や timeout では MAR を正当化できず、16 session 程度では certification 用モデルとして監査困難である。

### 推奨

A を採る。ただし P5 の「部分欠測なら session を落とす」だけでは不足する。

- correctness anomaly、arm 固有 timeout、nonzero、parse failure、throughput 不在は「欠測」ではなく candidate の substantive failure。削除・置換しない。
- 実走前 attestation failure、node loss、全 arm 共通の競合検出など、closed infra reason のみ session 全体を無効化できる。
- replacement は実走前に順序を固定した reserve list から自動選択し、最大試行数を超えたら `indeterminate`。
- 1 arm だけ、または残った rep だけを解析しない。全 arm ×全 5 rep が揃った complete session のみ paired 解析へ入れる。
- 無効 session の raw 値、理由、見えていた結果も全件 registry と材料レポートへ残す。
- final complete session 数が事前登録値未満なら、残数で救済解析せず `indeterminate`。

D126 が候補差し替えや workload 縮小を事後調整として拒否した原則と同型である `docs/decisions.md:6204`、`docs/decisions.md:6217`。

### 成果物影響

選択的欠測を捨てると session 分布、paired floor、RF、adjusted p が楽観方向へ動き、失敗 candidate が正例・certified 選択へ入る一方、全件性を失った proof chain が生成される。

### 入力 field の実在

既存 probe の `throughput.tsv` は成功値のみで、planned run、status、missing reason、replacement 関係を持たない。新出力要件は次である。

- `planned_runs[]` と `attempted_runs[]` の双射
- `run_status = observed | infra_invalid | substantive_failure`
- closed `reason_code`
- `returncode / timeout / verifier_status / competition_receipt_ref`
- `invalidates_rf_session`
- `replacement_for_rf_session_index`
- `analysis_set.complete_rf_session_indices`
- `planned_sessions / complete_sessions / invalid_sessions / reserve_sessions_used`

既存 `returncode` を欠測理由に二義化せず、構造化 `reason_code` を別に持つ。

## 規律 2 との関係

paired floor が小さくなること自体は正しさゲートの緩和ではない。RF は全 arm が独立に correctness gate を通過した後の性能識別であり、verifier anomaly を paired 統計で救済してはならない。規律 2 は anomaly の即 reject を要求する `CLAUDE.md:67`、`CLAUDE.md:71`。

小さい paired margin を certification に使える条件を閉表化する。

1. 全 arm が同じ `rf_session_index`、allocation、node、env、workload、records、threads、checkout、trace-disabled 条件に束縛されている。
2. arm 順序は事前登録した restricted randomization と exact match し、位置 balance・warmup/washout 規則を満たす。
3. 各 session に全 arm ×全 rep があり、session 間は別 allocation・事前固定した時間窓で独立している。
4. \(s_d^2=s_a^2+s_b^2-2s_{ab}\) を raw 値から再計算でき、floor の縮小が実在 covariance に帰属できる。
5. session、workload、candidate、欠測理由を結果から選ばない。
6. correctness status と `rf_acceptance_status` を別 field にし、前者が pass でなければ後者を計算しない。

一つでも破れたら `pairing_valid=false`、`rf_acceptance_status="indeterminate"` とし、certified 選択・正例 artifact・RF 材料主張へ流さない。自動 unpaired fallback は行わない。

## 必要な標本設計

裁定案としての最小値は、各 workload について **16 complete independent sessions ×各 arm 5 rep/session** とする。各 session は別 allocation とし、事前登録した複数時間窓へ分散させる。

理由は次のとおり。

- family が 2 workload ×3 contrast = 6 の場合、paired sign-flip の最小片側 p は \(2^{-J}\)、両側は \(2^{1-J}\)。8 session なら両側最小 p は 0.0078125 で、Holm の最初の閾値 \(0.05/6=0.00833\) を極端な完全整列時にだけ通せる。手続きは実行可能だが余裕がない。
- 8 session の sample SD の相対標準誤差は正規近似で約27%。既存コードも 8 session を「CV 推定の相対 SE 約27%」としている `orchestrator/campaign/between_run_floor.py:54`、`orchestrator/campaign/between_run_floor.py:56`。16 session でも約18%であり、これを下限とし、独立 pilot による power analysis がより大きい値を要求すれば増やす。
- 5 rep は session median を安定化する取得単位であり、独立標本数は増やさない。現行 between-run producer も 5 rep/session を使う `orchestrator/campaign/between_run_floor.py:54`、`orchestrator/campaign/between_run_floor.py:55`。
- 現存する 8-session calibration は baseline 1 arm だけなので、paired effect size、paired covariance、RF の power 設計には使えない。

したがって既存の 8 session は pilot、非常に大きく一貫した効果の生死確認、または floor の粗い偵察には使えるが、次は言えない。

- moderate な recovery を Holm 後に検出できること。
- denominator 近傍で bounded な Fieller 区間が得られること。
- workload 間 heterogeneity や非正規性が小さいこと。
- paired floor の tail または分散が十分精密であること。
- 1 session 欠測後も同じ事前登録検出力を保つこと。

## 事前登録の単位

単位は「1 candidate universe × exact workload set ×1 primary metric ×全 hypotheses/family ×1 schedule ×欠測・停止規則」を束ねた **1 RF confirmatory trial** とする。

実走前に、tracked な一枚の文書、例えば `docs/rf-preregistration/<rf_trial_id>.md` へ次をすべて埋めて commit する。

- arm identity、role、binary/source digest
- workload、env、metric、\(m/N/D/G/RF\) の推定量
- session 数、rep 数、allocation/time-window 設計
- exact cell manifest、candidate 上限
- randomization algorithm、seed、完全 schedule
- 帰無仮説、方向、family、alpha、Holm
- paired floor と \(\delta_D\)
- Fieller confidence level、境界分類
- missing/retry/reserve/停止規則
- power 根拠と全件報告規則

時点は「最初の candidate performance 値を見る前」、かつ schedule を実行へ渡す前である。空欄版を祖先に置いただけでは効力を持たないという既存整理に従う `docs/phase3-8c-preregistration.md:24`、`docs/phase3-8c-preregistration.md:33`。

成果物には `preregistration_commit`、`preregistration_path`、`measurement_checkout`、`schedule_sha256` を焼き、preregistration commit が結果 commit の祖先であることを検査する。これは D116 の「git commit された一枚の文書」「成果物から commit hash を参照」「ancestry で先後を証明」に一致する `docs/decisions.md:5494`、`docs/decisions.md:5502`。追加の凍結機構は不要である。

失敗後の candidate 差し替えは同じ trial の継続にしない。新しい事前登録 commit・新 trial ID とし、旧失敗を全件報告したうえで、親系列の candidate 上限と alpha-spending に従う。

静的なファイル確認と統計的論証のみを行い、pytest・build・benchmark は実行していない。

## 総括

- ① 帰無分布: session を独立 block、session 内の事前無作為化 arm label を交換する restricted randomization test を採る。
- ② 多重比較: primary throughput の全 workload ×全 acceptance contrast ×全正式 candidate を family とし、Holm で strong FWER 0.05 を制御する。
- ③ floor: arm marginal CV ではなく contrast 別 paired session 散布と adjusted decision marginを別名で持ち、pairing 不成立時は unpaired fallback せず判定不能にする。
- ④ 区間・帰属: Fieller を primary、block bootstrap等を sensitivity とし、denominator 不成立時は RF 非報告、clampせず区間全体で境界分類する。
- ⑤ 欠測: complete-block と closed infra reason に限定した置換を採り、arm 固有 failure は削除せず substantive failure、上限超過は判定不能とする。

親 brief への重大な反対は、(1) P1 の自動 unpaired fallback、(2) P2 の「session 自体を交換する」という表現、(3) P3 が candidate 軸と acceptance contrast 全体を family に含めていない点、(4) P4 の bootstrap-primary、(5) P5 が informative な arm 固有 failure まで session deletion で消せる点である。加えて、5 点の前提となる `S` の集約法が未裁定なので、「session median の平均の比」を同時に凍結する必要がある。