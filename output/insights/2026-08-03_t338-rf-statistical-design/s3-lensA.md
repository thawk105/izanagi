結論は **NO-GO**。段 2 は親案をかなり改善しているが、分母 gate 後の選択推論、weak-null randomization、多重性、必要標本数が互いに整合しておらず、現状では certified 受理の誤り率を保証できない。

### [real] RF の estimand が一意に決まっていない

段 2 は \(RF=E[N_j]/E[D_j]\) と「session median の平均の比」を採るが、これは未裁定の選択である。[s2-plan.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:7)

\(r_j=N_j/D_j\) とすれば、

\[
\frac{E[N_j]}{E[D_j]}=\frac{E[r_jD_j]}{E[D_j]}
\]

なので、これは degradation gap \(D_j\) が大きい session を重くする。一方 \(E[r_j]\) は session を等重みする。両者は \(r_j\) と \(D_j\) が関連すれば一致しない。また「事前登録した session 母集団」が、node・時刻・allocation のどの分布を指すかも未定義である。

**成果物影響:** session ごとの degradation gap が変動すると、同じ raw 値から RF 点値、`partial_recovery`、材料レポート記載値が変わる。

**修正案:** 「対象環境における総 throughput 回復率」なら ratio of expectations、「典型 session の回復率」なら別 estimand、と目的から択一し、node・時間窓・allocation の標本化分布も固定する。

### [real] 「分母が有意になるまで RF は未定義」は誤った状態分類であり、選択後推論を発生させる

既存 provisional 規則は「分母が noise floor に対して正に識別可能になるまで未定義」とし、段 2 も denominator LCB 不成立時に点値・区間を非報告とする。[ladder-design.md:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-07-29_t139-silo-degradation-ladder-design.md:171) [s2-plan.md:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:197)

しかし parameter \(\mu_N/\mu_D\) は、真の \(\mu_D\ne0\) なら定義される。標本から 0 と区別できないことは「未定義」ではなく「weak denominator で非認証」である。

さらに同じデータで分母を screen してから RF を報告すると、報告集合は \(\bar D\) が偶然大きい標本へ偏る。比推定量自体にも二次近似で

\[
\operatorname{Bias}\!\left(\frac{\bar N}{\bar D}\right)
\approx
\frac{\mu_N\operatorname{Var}(\bar D)}{\mu_D^3}
-\frac{\operatorname{Cov}(\bar N,\bar D)}{\mu_D^2}
\]

があり、screening 後の方向・大きさは保証できない。通常の区間の conditional coverage も失われる。これは一般的な significance filter の既知の帰結である。[van Zwet & Cator](https://arxiv.org/abs/2009.09440)

**成果物影響:** RF が報告された artifact だけで点値が偏り、Fieller の名目被覆率を満たさない `partial_recovery` や `stock_exceeding` が proof chain に入る。

**修正案:** \(\bar N,\bar D\) と unconditional な Fieller confidence set は常に出し、`weak_denominator_not_certifiable` とする。認証は \(D>\delta_D,N>0,G>0\) の同時 confidence region で行い、RF 報告自体を denominator gate に条件付けない。

### [real] 提案された randomization test は、実際の weak null に対して有限標本 exact ではない

検定対象は \(E[D_j]\)、\(E[N_j]\)、\(E[G_j]\) の片側 weak null だが、段 2 が有限標本 exact といえるのは Fisher sharp null のみである。[s2-plan.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:24) [s2-plan.md:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:34)

Studentization は平均効果 null を有限標本 exact に変えない。一般に、交換可能な同一分布 null では exact、parameter equality の weak null では漸近的妥当性に留まる。[Chung & Romano](https://arxiv.org/abs/1304.5939) J=16 を「十分」とする根拠はない。

arm 順序 randomize が保証するのは、明示した割付集合に対する位置効果の平均的均衡だけである。次を保証しない。

- session 間独立性
- arm 間 covariance の符号
- cache・温度・周波数の carry-over 不在
- arm 実行が後続 arm の潜在結果を変えないこと
- \(\delta_D\ne0\) の composite null に対する交換可能性

実 probe の W1 では stock が position 3 に3回、position 1に2回で、position 2には一度もない。[order.tsv:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/order.tsv:2) `shuf` は realized balance や washout を保証していない。

**成果物影響:** raw 値が同じでも帰無分布と adjusted p が変わり、正例 artifact と certified 選択の pass が反転する。

**修正案:** 割付可能 schedule 全体、位置・一次 carry-over balance、washout、sharp/weak null の区別を固定する。weak null を primary にするなら cluster-level 手続きの型 I 誤りを事前 simulation で較正する。

### [real] 多重比較 family は「一つの all-pass 受理」に対して過剰で、candidate 選択には不足する

partial recovery の global 受理が「全 workload で全条件を満たす」という一つの conjunction なら、その null は component null の和集合である。各 component を片側 \(\alpha\) で検定する intersection-union test だけで、偽 global 受理確率は \(\alpha\) 以下になる。6仮説への Holm は有効ではあるが、目的に対して過剰に保守的である。[s2-plan.md:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:80)

また \(D=N+G\) なので、\(\delta_D=0\) なら N、G が正である時点で D は正となり、三つを独立な family member のように扱うのは論理構造を無視する。一方、結果を見ながら candidate を替えて最終成功だけを certified 選択する場合は trial ID を替えるだけでは足りず、系列全体の alpha-spending が必要である。D126 も結果後の candidate 差し替えを禁止している。[decisions.md:6216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/docs/decisions.md:6216)

BH/FDR を採らない判断自体は正しい。FDR は一つでも偽の certified artifact が入る確率を制御しない。

**成果物影響:** Holm を global all-pass に使うと正例を不必要に減らし、逆に candidate 系列を family 外にすると偽成功 artifact が増える。

**修正案:** claim graph を分ける。global artifact は IUT、独立に公表する workload/cell 主張は Holmまたは closed testing、candidate 系列は事前登録した alpha-spending とする。

### [real] 「16 independent sessions が最小」は power 設計ではない

段 2 の16は sample SD の相対 SE 約18%から選ばれており、効果量・目標 power・最弱 component を使っていない。[s2-plan.md:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:293)

また仮説は片側なのに、標本数説明だけ両側 sign-flip の最小 p を使っている。[s2-plan.md:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:297)

| 仮定した手続き | 数値的下限 |
|---|---:|
| 片側 sign-flip + Holm 6、極端な全符号一致 | J=7 |
| 両側 sign-flip + Holm 6 | J=8 |
| 片側 IUT、各 component α=.05 | J=5 |
| 片側 α=.05/6、80% power、標準化効果 \(d=.5\) | 約42 |
| 同 \(d=.8\) | 約17 |
| 同 \(d=1.0\) | 約11 |
| IUTで6 componentの global power 80%をunion boundで確保、\(d=.5\) | 約49 |

power 行は正規近似 \(J\ge(z_{1-\alpha}+z_{.8})^2/d^2\) による楽観的下限で、小標本 t 補正、carry-over、欠測をまだ含まない。J=16 は Holm first-step で \(d\gtrsim0.81\) の大効果にしか component power 80%を期待できない。実際の restricted 3-arm schedule は sign-flip ではないため、最小 p も割付集合から再計算が必要である。

**成果物影響:** 16固定では moderate recovery を見逃して正例がゼロになる一方、稀に通った効果だけが過大評価される。

**修正案:** 独立 pilot から \(s_N,s_G,s_D\) と covariance を取り、最弱 component と global power を用いた事前 simulation で J を決める。8はpilot、16は大効果用であり、一般的最小値としない。

### [real] fresh CV の値は正しいが、paired floor と abort 一般化は導けない

記録値は確認できる。

- write-heavy: CV 0.6663%、8 session、abort 81.95%
  [rr5 JSON:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json:11)
- balanced: CV 1.0672%、abort 70.47%
  [rr50 JSON:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr50_rmw0.json:11)
- read-heavy: CV 0.1098%、abort 16.03%
  [rr95 JSON:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json:11)

しかし全て一つの baseline arm の back-to-back session median であり、コード自身が settle は独立性を足さず、cold-boot・温度・時間ドリフトを含まない下限とする。[stability.py:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/orchestrator/calibrator/stability.py:102)

paired 差には

\[
\operatorname{Var}(A-B)=\operatorname{Var}(A)+\operatorname{Var}(B)-2\operatorname{Cov}(A,B)
\]

が必要で、これらの JSON は covariance を一切持たない。正 covariance なら縮小するが、負なら増える。さらに分母 gap が小さければ、絶対 SD が縮んでも \(s(D)/\bar D\) は発散し得る。「paired なら floor が小さくなる」は支持されない。

abort 率との一般化も成立しない。abort 82% の write CV 0.666%より、abort 70.5% の balanced CV 1.067%の方が大きい。3 workload各1系列では因果・単調関係を識別できない。D19 の既存記述はRFへ一般化できない。[decisions.md:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/docs/decisions.md:337)

**成果物影響:** この一般化で paired margin を小さくすると、弱い分母や recovery gap が誤って識別され、正例・材料レポート・proof chain の受理集合が増える。

**修正案:** workload・contrast ごとの paired pilot を新規取得し、raw covariance、paired SD、その不確実性を保存する。既存3 CVは参考記述に限定する。

### [refuted] 「別 allocation でなければ D19 の再演」は統計的に強すぎる

追補 B は paired 単位を別 allocation に限定する。[brief-addendum.md:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/brief-addendum.md:40)

allocation ID は独立性の必要十分条件ではない。同一 allocation 内でも十分離れた randomized block が mixing 条件を満たせば独立近似は可能であり、別 allocation でも同じ node・連続時間窓・持続する熱状態なら相関し得る。ただし estimand が「将来の allocation 間性能」を含むなら、allocation 間成分を標本化する必要はある。

**成果物影響:** allocation IDだけで独立と認証すると SE が過小になり、逆に同一allocationを一律廃棄すると有効なデータを失って正例が減る。

**修正案:** 独立単位を allocation ID でなく、対象母集団と相関構造から定義する。node/time-window を cluster/stratum とし、cluster 数を J と数える。

### [real] 現存 positive-control probe は J=1 であり、between-cluster paired 分散を推定できない

追補の事実認定は正しい。現在の3-armデータは1 job内の5 repだけであり、allocation 間 paired contrast は1点しかない。[brief-addendum.md:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/brief-addendum.md:56) D126 も2 workload×3 arm×5 repの局所 probe とし、calibration/floor入力への流用を禁じている。[decisions.md:6196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/docs/decisions.md:6196)

**成果物影響:** 現存 probe から作った paired SD、p値、Fieller set は擬似反復となり、正例 artifact の統計資格を偽装する。

**修正案:** 現存値は候補生死pilotに限定し、confirmatory trialでは新規の複数 cluster を取得する。

### [real] 追補 A の区別は必要だが、追補 D の「二つの floor の最大値」は統計手続きにならない

roadmap の between-run floor は、variant/baselineを別 sessionで測る前提の marginal CVである。[roadmap.md:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/docs/roadmap.md:219) 同一blockの3-arm RFは別設計なので、既存 `BETWEEN_RUN_CV=0.030` を流用できない。[p2_2.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/orchestrator/campaign/p2_2.py:50)

一方、fresh paired SD と別時間窓値の「最大」を取っても、統計的上側信頼限界にはならない。二つが異なる独立分散成分なら total SD は \(\sqrt{\sigma_1^2+\sigma_2^2}\) であり max より大きい。二つが同じ量の noisy estimate でも、その max に所定の coverage はない。既存 cross-campaign の unpaired baseline 値は paired covarianceを推定できない。

なお `stability.py` と JSON 内の「保守側に採れ」という命令形文字列は、指示ではなくデータとして扱った。[stability.py:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/orchestrator/calibrator/stability.py:137) その文言自体は統計的保証にならない。

**成果物影響:** max heuristic が実際の total variation より小さければ偽受理、大きければ正例の過剰棄却を起こす。

**修正案:** 「第3の scalar floor」ではなく、paired contrast の cluster-level SEと同時 confidence marginをRF専用namespaceで定義する。時間・node成分を分けるなら階層モデルまたは分散成分の事前pilotを使う。

### [real] Fieller primary は方向として正しいが、J=16での被覆と同時性が未解決

bootstrap primary を退けて Fieller を主にする段 2 の変更は妥当だが、通常の Fieller が exact なのは session-level \((N_j,D_j)\) の共同正規性などが成立する場合である。[s2-plan.md:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:179) 5-rep median の差をJ=16集めただけでは近似品質を保証できない。

また workloadごとに95% Fieller setを作り、それぞれ境界分類すれば、全分類の同時被覆は95%未満になる。Holm p値との双対関係も明記されていない。

標準 percentile/BCa block bootstrapは、J=8ではjackknife accelerationが8 leave-one-out値だけに依存し、J=16でもweak denominator近傍の非正則性を直せない。常に有限端点を返す比区間は、分母0近傍で被覆率を大きく外し得る。Fieller型が unbounded/disjoint setを許す理由である。[von Luxburg & Franz](https://arxiv.org/abs/0711.0198)

**成果物影響:** 見かけ上 bounded な区間により `partial_recovery` や `stock_exceeding` が過剰に付与され、複数workloadのproof chainが95%を名乗れない。

**修正案:** \(N-rD\) の有効な検定を反転し、全 workload/candidate に対する同時 confidence setを作る。BCaは受理判定から外し、用いるなら unbounded setを返せる geometric bootstrapだけを感度分析にする。

### [real] complete-session 規則と reserve replacement は MNAR を直さない

段 2 は closed reason codeを導入するが、complete case が妥当なのは inclusion が対象 outcome・割付に依存しない条件下だけである。[s2-plan.md:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:232)

例えば thermal overload、arm固有timeout、parse不能が低throughputと関連すれば、session全体を削除しても欠測はMNARのままである。「全arm共通の競合検出」も、結果を一部見た後なら outcome-blind ではない。reserveで置換して完全数を満たしても、残ったsession分布は選択済みである。現行実装が `None` を除外するだけなのはRFには使えない。[stability.py:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/orchestrator/calibrator/stability.py:118)

correctness anomalyは欠測処理ではなく即 reject、performance timeoutは事前定義した複合失敗endpointまたはworst-case boundに含めるべきである。

**成果物影響:** 低性能・不安定sessionが解析集合から消え、RF、paired SD、adjusted pが楽観化し、失敗candidateが正例へ入る。

**修正案:** 結果取得前に外部証拠で確定するinfra failureだけ置換可とする。post-start欠測はartifact reject/indeterminateを既定とし、必要ならworst-case boundsとMNAR sensitivityを併記する。

### [real] P1 の自動 unpaired fallback は fail-closed ではない

brief は pairing不成立時に同じmeasurementをunpairedへ戻すとしている。[brief.md:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/brief.md:40)

同じsession内で得たarmsは相関しており、独立標本用 \(\sqrt{s_a^2+s_b^2}\) は正 covarianceなら保守的でも、負 covarianceなら真の差分散を過小評価する。metadata不備やschedule不一致も、統計的独立への変換ではない。段 2 が automatic fallback を拒否した点は正しい。[s2-plan.md:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:157)

**成果物影響:** fallback後のSEとp値が誤り、同じ不適格データが別名でcertified受理へ流れる。

**修正案:** pairing不成立は `indeterminate`。unpaired解析は別の事前登録・独立収集データだけで行う。

### [real] preregistration ancestry だけでは「値を見る前」を証明できず、trial ID更新は選択性を消さない

D116 はcommit ancestryに加え、全runと材料レポートの双射検査を要求する。[decisions.md:5494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/docs/decisions.md:5494) [decisions.md:5504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/docs/decisions.md:5504)

planの ancestry は「事前登録commitが結果commitより先」を示すが、外部raw値が事前登録commit前に既に生成・閲覧されていないことまでは示さない。また失敗ごとに新trial IDを発行しても、最終成功を選ぶ系列全体のalphaはresetできない。[s2-plan.md:327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:327)

**成果物影響:** 失敗trialが形式上分離され、成功candidateだけがcertified選択・材料レポートへ残るfile-drawer経路が残る。

**修正案:** prereg commitを参照するmeasurement-start receipt、親系列ID、candidate上限、alpha-spending、全attempt双射を一体化する。

### [refuted] floor gate と検定を AND で直列化するだけでは型 I 誤りは増えない

有効な検定 \(B\) に対し受理条件が `floor pass A AND B reject` なら、偽受理集合 \(A\cap B\) は \(B\) の部分集合なので型 I 誤りは増えず、通常は保守化・power低下を起こす。

問題になるのは、floor通過後だけfamily・区間・報告対象を変更する選択推論であり、単なるAND gateそのものではない。段 2 が物理SDとdecision marginを分けた方向は妥当である。[s2-plan.md:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:148)

**成果物影響:** この点を誤って追加alpha分割すると正例だけが不必要に減る。受理集合の偽陽性増加ではない。

**修正案:** SDは記述値、認証は一つのLCB/test-inversion手続きに統合し、同じ証拠を二重gateと呼ばない。

### [refuted] clamp禁止と `RF>1` の機序非帰属は維持すべき

点値を \([0,1]\) にclampすると below-degraded と stock-exceeding の証拠を消すため、禁止は正しい。`RF>1` だけで「新規改善」や回復機序を主張せず、ablationを要求する判断も妥当である。[brief.md:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/output/insights/2026-08-03_t338-rf-statistical-design/brief.md:48)

ただし分類は点値ではなく、multiplicity-adjusted confidence set全体が境界の片側にある場合だけに限る。

**成果物影響:** この規則を崩すと材料レポートの方向・機序記述が改変される。維持すれば受理集合は不当に増えない。

**修正案:** clamp禁止・非帰属を維持し、unbounded/disjoint/0または1を跨ぐsetは一律 `indeterminate_boundary` とする。

### [refuted] P6 の Phase 2 Gate1 √2 問題の分離はRF設計を壊さない

既存 `compare()` はCVが一測定の散布で、独立差のSDは \(\sqrt2\) 倍になる既知問題を明記している。[stability.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/orchestrator/calibrator/stability.py:238) しかしRF専用のpaired inferenceへその `noise_cv` を渡さない限り、既存reportとの互換問題を本waveから分離できる。

D120の「正例artifact完成までcomputeをlandしない」というdocs-only境界も統計設計の検討を妨げない。[decisions.md:5756](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-statdesign/docs/decisions.md:5756)

**成果物影響:** P6を維持する限り既存certified選択・材料レポートは不変。RFへ既存3%を流用した場合だけ新受理集合が壊れる。

**修正案:** P6を維持し、RF namespace・producer・consumerから既存 `noise_cv` を型レベルで排除する。

## 判定

**判定: NO-GO**

plan v2へ進む最低条件は次のとおり。

1. ratio-of-expectations と平均session RFのどちらをestimandにするか裁定する。
2. denominator screeningによる非報告を廃止し、unconditionalなjoint/Fieller confidence setへ統合する。
3. sharp null・weak null・carry-over・実割付集合を固定する。
4. global IUT、個別主張FWER、candidate系列alpha-spendingを分離する。
5. paired pilotから効果量・covarianceを得てJを再設計する。16を一般的最小値にしない。
6. post-start欠測をMNARとしてfail-closedに扱う。
7. measurement-start receiptと全attempt双射をpreregistrationに追加する。

静的確認と統計的論証のみであり、pytest・build・benchmarkは実行していない。

## 総括

- 分母gate後だけRFを報告する規則は選択バイアスとconditional undercoverageを生み、「未定義」という状態名も誤り。
- ratio-of-expectationsはdegradation gap加重estimandであり、平均session回復率との択一が未裁定。
- restricted randomizationはweak mean nullに有限標本exactではなく、arm順序randomizeもcarry-over・session独立性を保証しない。
- Holm 6仮説はglobal all-passには過剰だが、candidate系列の選択性には不足する。
- 16 sessionsはpower根拠を持たず、moderate effect \(d=.5\) なら概算42〜49 clusterが必要。
- fresh CV 3値は正しい記録だが、paired covariance・paired floor・abort率との因果を一切識別しない。
- allocation IDは独立性の必要十分条件ではない一方、現存J=1 probeからbetween-cluster分散は推定不能。
- fresh値とcross-window値の最大を取る手続きは分散合成でも上側信頼限界でもない。
- standard Fiellerの小標本被覆、複数workload同時性、BCaのweak-denominator非正則性が未解決。
- complete-session deletionとreserve replacementは結果依存欠測を除去せず、randomization分布も壊す。
- P1の同一データへのunpaired fallbackは負 covariance時に反保守的となる。
- git ancestryだけではraw値未閲覧を証明せず、新trial IDだけでは反復candidate選択のalphaを制御しない。