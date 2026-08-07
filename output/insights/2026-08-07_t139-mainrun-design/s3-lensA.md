**NO-GO — 現行 brief / 段2プランのまま本走を投入してはならない。**

## 総括

直接の誤認証経路は、brief の P3 が `G>0` と Fieller を受理条件から外しており、stock 超過候補を正例にできる点である。段2プランはこれを修正したが、J の「99% assurance」は Monte Carlo 誤差しか覆わず、pilot 推定・候補 J 選択・6成分同時性を覆っていない。

さらに、6 rep の中央値を採りながら平均用の `σ_W²/r` を使い、J=1 probe の within-cluster SDを primary contrast の allocation 間設計へ流用している。Q2 の相対分母条件、Fieller と同時領域の関係、候補系列の alpha 台帳も未確定である。

### 1. [blocker] brief P3 は stock 超過候補を誤って認証できる

[判定] brief の `N>0 ∧ D>δ_D` だけを primary とし、`G>0` と Fieller を受理条件から外す案は棄却必須である。

[根拠: [brief.md:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-07_t139-mainrun-design/brief.md:44)、[package.md:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-03_t338-rf-statistical-design/package.md:261)、[D162:8031](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/docs/decisions.md:8031)] `D=N+G` なので、`N>0` と十分大きい `D` は `G≤0`、すなわち `X≥stock` を排除しない。Q9 は Fieller 全体が `(0,1)` 内にある場合だけ partial recovery とする。

[成果物影響: `rf_positive_artifact`] brief のままなら `RF≥1` の候補が正例になり得る。

[最小の直し方] 段4で P3 を明示的に棄却し、少なくとも `N>0 ∧ (D−κS)>0 ∧ G>0` を global predicate に固定する。Fieller との重複は所見6のとおり一貫した構成にする。

### 2. [blocker] `d_plan` の planning bound は6成分同時の下限ではない

[判定] `Δ⁻/σ⁺` は、正規・独立 cluster を仮定しても現状では marginal bound の比にすぎず、global planning assurance を与えない。二重計上より、同時性と共分散不確実性の過小計上が問題である。

[根拠: [s2-plan.md:117](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:117)] 正しい片側 \(1-\alpha\) bound は

\[
\sigma_U=s\sqrt{\nu/\chi^2_{\alpha,\nu}},\qquad
\Delta_L=\bar\Delta-t_{1-\alpha,\nu}s/\sqrt{J_p}.
\]

プランは `γ` を「planning confidence」と呼びながら下側 tail probability の位置に置く。`γ=.99` と読めば両 bound の向きが逆になる。`γ=α` と読んでも、1成分につき平均・SDの2 bound、6成分で計12 bound なので、単純 union bound の同時被覆は最大でも \(1-12\alpha\)。Jp=8による6次元 covariance も実質7自由度しかなく、相関の不確実性は bound に入っていない。

[成果物影響: `d_plan`, `J_main`] `d_plan` を真の最小効果の保証値として使うと、Jを過小決定できる。逆方向には不必要な `design_not_feasible` を増やす。

[最小の直し方] `α_plan` を tail probability として明記し、各 \(d_k\) の noncentral-t inversion等による同時下限、または平均ベクトル・共分散の共同信頼集合上の least-favourable power を使う。正規モデルを使うならその仮定も事前登録する。

### 3. [blocker] simulation の99% LCBは真の検出力の99%下限ではない

[判定] Bを増やしたとき一致するのは、pilot plug-in 分布に条件付けた simulation probabilityだけである。Jp=8を固定したままでは真の検出力の一致推定量にならない。

[根拠: [s2-plan.md:135](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:135)] `pilot共分散`を固定し、\(B=10^6\) の二項 Monte Carlo LCBを取っている。Bはsimulation誤差を減らすが、pilot平均・分散・相関、分布モデル、carry-overモデルの誤差を減らさない。また `11..J_max` の複数Jから最初の通過値を選ぶため、Jごとの99% LCBは選択後のJについて99%同時保証にならない。

[成果物影響: `LCB99(power)`, `J_main`] 表示上は `LCB≥.80` でも、真のglobal powerが.80未満になり得る。

[最小の直し方] pilot parameterの共同信頼集合上で最悪powerを評価するか、pilot再標本化を含む外側simulationでassuranceを定義する。候補J全体には同時Monte Carlo band、Bonferroni、またはconfidence sequenceを使い、LCB方式も固定する。

### 4. [blocker] `d_plan=min(1,…)` と `design_not_feasible` の閉じ方が不足している

[判定] `min(1.0,…)` は切り上げではなく、効果を1以下へ切り下げる操作なので、それ自体は楽観化しない。ただし1個のscalar dではFiellerを含む受理確率を一意に定められない。`design_not_feasible` も、現在の文面だけでは再pilot・`J_max`引上げを閉じていない。

[根拠: [s2-plan.md:129](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:129)、[s2-plan.md:143](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:143)、[brief.md:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-07_t139-mainrun-design/brief.md:23)] 同じ最小marginal dでも、6成分の相関、N/Dの位置、Fieller形状によりglobal powerは異なる。

[成果物影響: `J_main`, attempt registry] pilot結果を見て `J_max` やpilot本数を変更すれば、事前固定式ではなく結果依存の設計更新になる。

[最小の直し方] pilot前に平均ベクトルをleast-favourable pointへ写す規則、`J_max`、pilot attempt数、再設計禁止を固定する。`design_not_feasible` はexact candidate／parent familyの終端状態とし、再開は全attemptを保持した新study・新alpha spendingに限定する。

### 5. [blocker] 中央値に `σ_W²/r` は使えず、`k≤0.408` は選んだ推定量と不整合

[判定] `k≤0.408` と `k≤0.949` の代数は、iid残差の算術平均モデルに限れば正しい。しかし6 rep中央値には適用できない。

[根拠: [s2-plan.md:99](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:99)、[s2-plan.md:161](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:161)] 一般には

\[
\operatorname{Var}(m_j)=\sigma_B^2+a_r\sigma_W^2,
\]

であり、中央値の \(a_r\) は残差分布と偶数中央値の定義に依存する。連続分布の標本中央値でも漸近分散は \(1/(4rf(\mu)^2)\) で、正規なら約 \(\pi\sigma_W^2/(2r)\) である。5→6 repで11を10以下にする条件は

\[
k^2\le 10a_5-11a_6.
\]

平均の \(a_5=1/5,a_6=1/6\) を代入した場合だけ \(k\le\sqrt{1/6}=0.408\)。5→10の0.949も同様に平均モデル限定である。

[成果物影響: rep数、`σ_B`閾値、`J_main`] W1 `0.00235` / W2 `0.00149`という閾値は成立せず、6 rep採用とJ節約量が反転し得る。

[最小の直し方] arm代表値を算術平均へ戻すか、pilotで選んだ中央値そのものの \(a_5,a_6\) とarm間共分散を推定する。N、`D−κS`、Gごとにrep感度を出す。

### 6. [blocker] 同時領域とFiellerの「不一致」は、共通構成を定義しない限り統計的不整合ではない

[判定] AND自体は型I誤りを増やさず、別手続きなら保守側へ受理集合を縮めるだけである。ただし現在は「冗長なchecksum」なのか「別の第二gate」なのかが未定義である。

[根拠: [s2-plan.md:192](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:192)、[s2-plan.md:203](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:203)、[s2-plan.md:227](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:227)] 同じsample covarianceと同じcritical value \(q\) から構成すれば、Fiellerの \(r=0\) 検査はN、\(r=1\) 検査は \(N-D=-G\) の検査である。したがって `LCB(N)>0 ∧ LCB(G)>0` と「bounded Fieller集合が `(0,1)` 内」は同値になり、ANDは受理集合を変えない。異なるq、randomization region、片側／両側規則を使えば正当な不一致が発生する。

[成果物影響: `statistical_inconsistency`, `fieller_ok`, J power] 正当なmethod disagreementをraw破損扱いしてfalse negativeを増やすか、simulationとvalidatorで異なる受理集合を実装し得る。

[最小の直し方] Fiellerを同じ同時領域のratio projectionとして導出し、qとtruth tableを共通化する。別手続きとして残すなら「dual-gate」と明記し、不一致は `not_certifiable` とする。非有界・非連結ではlower/upper比較をせず、既裁定のshape状態でfalseにする。

### 7. [blocker] `E[D−κS]>0` はQ2の一解釈とだけ同値である

[判定] Q2の「stock比」が

\[
\theta_D=\frac{E[D]}{E[S]}>\kappa,\qquad E[S]>0
\]

を意味するなら、`E[D−κS]>0` は厳密に同値であり、plug-in閾値より正しい。一方、`E[D/S]>\kappa` や固定reference stockに対する絶対 `δ_D` とは別母数である。裁定原文はここまで特定していない。

[根拠: [package.md:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-03_t338-rf-statistical-design/package.md:77)、[s2-plan.md:109](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:109)] packageは単位を「stock比」とだけ定め、ratio-of-expectationsかexpectation-of-ratioかを閉じていない。brief P4のprobe値からκを選ぶ案は、probe自身がfloor入力を禁じる [preregistration.md:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/preregistration.md:124) と衝突する。

[成果物影響: `κ_w`, H contrast, 受理集合] 同じrawでも採る母数とκにより `H=D−κS` の符号が変わる。

[最小の直し方] Q2を `E[D]/E[S]` と明文化し、候補非依存のκをpilot前に裁定する。Sを固定値扱いせず、

\[
\operatorname{Var}(D-\kappa S)
=\operatorname{Var}(D)+\kappa^2\operatorname{Var}(S)
-2\kappa\operatorname{Cov}(D,S)
\]

およびN/Gとの共分散を共同領域へ入れる。RFのFieller分母DにもS由来の変動が既に含まれる。

### 8. [nit] primary失敗後のHolm公表は、条件付きで直ちに無効とは限らない

[判定] 6 cell familyを事前固定し、primary結果に関係なく全6個へHolmを適用するなら、primary失敗後に個別棄却を公表しても無条件strong FWERは保たれる。同じrawの再利用自体は違反ではない。

[根拠: [s2-plan.md:180](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:180)、[package.md:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-03_t338-rf-statistical-design/package.md:205)] 公表された偽棄却は、6個へ事前適用したHolmの偽棄却事象の部分集合である。ただしprimary失敗を見てcellや区間を選ぶと、条件付きcoverageと効果量表示は選択される。

[成果物影響: 個別cell公表] significant cellだけを抜き出すと、certified artifactではなくても材料レポートが成功だけを強調する。

[最小の直し方] primary成否にかかわらず、6 cellすべての調整済みp値・同時区間・失敗を固定表で公表する。cell成功をartifact適格性や候補昇格へ接続しない。

### 9. [blocker] 候補系列alphaと個別cell familyの接続が閉じていない

[判定] 候補ごとにprimary用alphaだけをspendし、個別6 cellへ毎回Holm `.05` を再投入すると、候補系列全体の個別公表FWERが膨張する。

[根拠: [s2-plan.md:184](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:184)、[s2-plan.md:428](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:428)] 「累積alpha台帳」は書かれているが、global IUT、cell Holm、候補系列のどのfamilyへ何をspendするかは未定で、裁定項目のままである。

[成果物影響: false public claim / candidate promotion] trial IDの更新によりcell claimのalphaを事実上リセットできる。

[最小の直し方] primary系列とcell公表系列に別々の累積台帳を置くか、候補×6 cellを含む単一closed familyを定義する。各candidate投入前にspent alphaを固定する。

### 10. [blocker] J=11とJ=13は別のpower目標であり、どちらも既裁定値とは断定できない

[判定] J=11はQ5パッケージにある「α=.05/6で各component power 80%」の概算に一致するが、global conjunction power 80%を保証しない。J=13はIUT各成分α=.05、各成分のtype-IIを `.20/6` 以下にするunion-bound案と整合するが、新しいglobal power目標である。

[根拠: [package.md:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-03_t338-rf-statistical-design/package.md:155)、[s2-plan.md:145](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:145)、[brief.md:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-07_t139-mainrun-design/brief.md:21)] briefが固定しているのは `d≈1.0` と二段階・事後追加禁止であり、component 80%かglobal 80%かは固定していない。

[成果物影響: `J_main`, point上限] 11と13で最低2 allocation変わり、t補正・Fieller・carry-overを含めれば13より増える可能性もある。

[最小の直し方] 「global acceptance probability 80%」か「各component 80%」かをユーザー裁定へ戻す。global 80%ならJ=13はz近似の保守的sanity値であり、最終Jは修正済みassurance手続きで決める。

### 11. [blocker] probeの巨大なwithin-cluster dは「d=1が保守的」の根拠にならない

[判定] 親の算出値はrawの記述統計として正しい。しかしcluster間設計への一般化はできない。

[根拠: [throughput.tsv:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/throughput.tsv:2)、[brief.md:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/insights/2026-08-07_t139-mainrun-design/brief.md:54)、[preregistration.md:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-mainrun-design/output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/preregistration.md:132)] 再計算すると、RF SDはW1 `0.0057458`、W2 `0.0036626`、paired contrast dも提示値どおりである。しかし5 repは1 allocation内の固定scheduleであり、\(\sigma_B\)、cluster母平均、cross-workload covarianceを1点も推定しない。mainの

\[
d_{\rm cluster}
=\frac{E[\Delta_j]}
 {\sqrt{\sigma_B^2+\operatorname{Var}(m_j\mid j)}}
\]

の分子・\(\sigma_B\)はいずれも未識別である。

iid Gaussianを仮定してさえ、n=5のSDはdf=4で、95% CIは観測SDの約 `[0.599, 2.874]` 倍、SDの相対SEは約35%。RF SDならW1約 `[0.00344,0.0165]`、W2約 `[0.00219,0.0105]` である。固定順序・carry-overがあればこの区間自体も保証されない。

[成果物影響: `d_plan`, rep配分, `J_main`] within dから「d=1は保守的」と宣言すると、未観測のallocation間変動をゼロ同然に扱い、Jを過小決定する。planは [s2-plan.md:159](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:159) で一度この限界を認めながら、同SDを [s2-plan.md:174](/work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:174) のcluster閾値へ再利用しており不整合である。

[最小の直し方] probeから主張してよいのは「この1 allocationではengineering separationが大きく、観測within scatterが小さかった」までとする。d=1、cluster covariance、rep対J配分はexternal pilotのallocation-level `N/H/G` から新たに決める。

## 未検証の懸念

- allocation間の正規性・exchangeability、powerのJに対する単調性、washout後の残差独立性はデータ未取得で未検証である。上記blockerの根拠には数えていないが、pilot診断と感度分析へ事前登録すべきである。
- simulation実装はまだ提示されていないため、nested uncertaintyや共通乱数が将来実装で補われる可能性はある。ただし現行プラン本文からは保証できない。

静的検査のみで、テスト・build・simulation・Pegasus実走は行っていない。