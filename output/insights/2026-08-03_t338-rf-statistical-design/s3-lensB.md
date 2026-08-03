判定は **NO-GO**。統計案以前に、既裁定・実行契約・consumer・標本設計が一つの実行可能な裁定へ閉じていない。

### **[real] 16 allocation 案は現行 formal campaign 契約では実行不能**

段 2 は「16 complete independent sessions、各 session は別 allocation」を要求するが、Pegasus 契約は `single_process=True / allow_resume=False`、すなわち campaign を単一 allocation/node/process で完遂する契約である。追補 D は J 本を不要とするが、現存 3-arm データは J=1 で、代用するとした cross-window paired データも存在しない。
根拠: `output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:291-300`、`orchestrator/campaign/env_contract.py:180-191`、`docs/pegasus-runbook.md:432-434`、`output/insights/2026-08-03_t338-rf-statistical-design/brief-addendum.md:56-61,80-86`

**成果物影響:** 現行経路では正例 artifact は生成不能、ad-hoc に複数 job を束ねれば proof chain の trial 完全性が成立しない。

修正案: 「G12 を supersede」「1 allocation = 1 immutable subcampaign として新しい trial aggregator が束ねる」「単一 allocation の fresh 下限＋事前固定した cross-campaign 系列」の三択を明示する。第三案も cross-window の本数・時点・集約規則を事前固定し、新規データ取得を要求する。

### **[real] paired 採用は D19 の例外新設であり、D104 は supersede 根拠にならない**

roadmap と D19 は variant/baseline を同一 session で測らないことを明記している。D104 の paired 比較は受入全走施策の一次証拠に限定され、A-B/B-A と機構実発火の直接観測まで要求する先例であって、RF floor の既裁定変更ではない。追補 A は衝突を認識したが、段 2 の推奨 A には roadmap 改訂と D19 の適用範囲変更が原子的に結び付いていない。
根拠: `docs/roadmap.md:219-225`、`docs/decisions.md:329-337`、`docs/decisions.md:4658-4663`、`output/insights/2026-08-03_t338-rf-statistical-design/brief-addendum.md:22-31`、`output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:146-159`

**成果物影響:** 同じ raw 値を既存 3% floor と新 paired margin のどちらで判定するかにより、正例・certified 選択の受理集合が反転する。

修正案: 選択肢 A を「第3種の測定クラス新設＋roadmap §3.6 改訂＋D19 の該当前提を明示的に限定/supersede」と一体化する。ユーザー合意後の roadmap 改訂は協議改訂の手続きに従う (`docs/roadmap-history/README.md:20-27`)。

### **[real] 「fresh CV が 3% 未満だから paired floor は小さくできる」という一般化は支持されない**

0.11〜1.07% は linux-baremetal 上の単一 baseline arm・同一時間窓・back-to-back 測定の marginal CV である。arm 間 covariance、paired contrast、Pegasus の allocation 間ドリフトを一切測っていない。コード自身も settle は独立性を足さず、fresh 値は下限だと認める。さらに wired 3% は n=2 の cross-campaign CV と別量の high-abort within-run 最大値を混ぜたヒューリスティックで、統計的上限ではない。
根拠: `output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json:33-52`、`output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr50_rmw0.json:33-52`、`output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json:33-52`、`orchestrator/campaign/between_run_floor.py:14-17,86-92`、`orchestrator/calibrator/stability.py:110-115`、`orchestrator/campaign/p2_2.py:54-62`、`docs/roadmap.md:348-349`

**成果物影響:** 未観測 covariance を正と仮定して margin を縮めると、正例および certified 選択が偽陽性方向へ増える。

修正案: 数値方向の主張を削除する。同一 env・同一 protocol の allocation/time-window 間で contrast 別 covariance を測り、負 covariance も許した事前固定の信頼上限または検定で判定する。

### **[real] 追補 C の「Layer3 に第3 floor kind を足す」だけでは、置き場所自体が誤る**

Layer3 の calibration floor 検索は `(records, threads, workload)` だけで照合する。一方、段 2 の paired SD は candidate・arm contrast ごとの trial 固有統計である。閉表だけ広げると candidate を識別できず、同じ floor の誤流用または複数 match エラーになる。
根拠: `orchestrator/campaign/layer3_report.py:213-231,251-300`、`orchestrator/campaign/layer3_schema.json:16`、`output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:128-151,165-169`

**成果物影響:** 材料レポートに誤った paired floor が載るか floor が欠落し、RF proof chain の根拠値が壊れる。

修正案: env calibration と trial 固有 RF 統計を分離する。RF は versioned trial/WAL 区画へ `trial × candidate × workload × contrast` キーで置き、Layer3 schema・generator・双射検査を同時に更新する。

### **[real] producer から certified consumer までの経路が無く、統計 gate を作っても発火しない**

適格性権威は D126 により未裁定で、ledger は現在も recovery/pipeline 不適格を exact に要求する。Layer3 は既存 campaign.lock/WAL の既知 stage を射影するだけで、提案された RF session、欠測 registry、p 値、Fieller set、`rf_acceptance_status` を消費しない。
根拠: `docs/decisions.md:6184-6189`、`patches/ledger.json:14-17`、`orchestrator/campaign/silo_ladder_rung1_contract.py:538-550`、`orchestrator/campaign/layer3_report.py:380-427`、`orchestrator/campaign/layer3_schema.json:5-22`

**成果物影響:** 裁定しても certified 選択・材料レポート・proof chain・正例受理集合は変わらない。逆に producer 自己宣言を接続すれば権威境界を迂回する。

修正案: 後続 scope として、計測 producer、attempt registry、schedule validator、RF calculator、[T-337] eligibility authority、Layer3 vNext、selector/material-report consumer、双射・変異検査を明記する。

### **[real] `pairing_valid` 等を field にするだけでは gate にならない**

段 2 は `pairing_valid`、`run_status`、`rf_acceptance_status` を提案するが、誰が raw receipt から導出するかを定めない。D127 は caller の enum/bool 自己申告が検出器でも意味 gate でもないと既裁定している。現行 Layer3 の `_view_row` は payload をそのまま写す。
根拠: `output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:261-289`、`docs/decisions.md:6252-6256`、`orchestrator/campaign/layer3_report.py:208-210,395-425`

**成果物影響:** producer の誤実装または自己宣言一つで正例・certified 選択が増え、proof chain が恒真保証になる。

修正案: status は allocation receipt、raw runs、schedule、checkout、reason code から独立 validator が再計算する。validator identity/hashと再計算結果を artifact に束縛し、宣言値との不一致を拒否する。

### **[real] 「5点パッケージ」ではなく、未提示の追加裁定が受理条件を支配する**

段 2 は新たに「session median の平均の比」、primary endpoint、5 rep を選んでいる。さらに `LCB(\bar D)>\delta_D` を必須判定に使う一方、`\delta_D` の値・単位・導出規則を「別裁定」として残す。これは択一なしの親決定または未決定の第6点以降である。
根拠: `output/insights/2026-08-03_t338-rf-statistical-design/brief.md:16-18`、`output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:3-18,148-153,195-198,316-324`

**成果物影響:** 推定量または `\delta_D` の選び方だけで RF 値、denominator 成立、正例受理が変わる。

修正案: estimand と `\delta_D` を明示的な追加裁定にする。値、TPS/相対量の別、workload 別か共通か、変更手続きを選択肢として提示する。

### **[real] J=16 の根拠は選んだ検定・family と一致せず、費用裁定にもなっていない**

推奨は session 内の実 schedule を再現する restricted randomization だが、J=16 の根拠は別の paired sign-flip の最小 p である。また family は全 candidate を含めるとした直後に、標本設計では「2 workload×3 contrast=6」と固定している。既存 1-allocation probe は30性能run＋livenessで176秒だが、未較正の10k/100k records であり、16 allocation の正式費用・queue・reserve・pilot増分の上限を示さない。
根拠: `output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:34-48,103-107,291-300`、`output/insights/2026-08-02_t139-positive-control-probe/README.md:59-62,79-81`、`output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/t139_positive_control_probe.pbs.e877859:3-14`

**成果物影響:** J不足なら adjusted p/区間が成立せず正例が判定不能、結果後の追加 J は受理集合を事後変更する。

修正案: 最終 family・candidate cap・restricted schedule を先に固定し、その正確な randomization space と pilot covariance で power を設計する。J、reserve、最大 J、時間窓、quota/queue 予算を一つの選択肢にする。

### **[real] 新 trial ID による candidate 差し替えは多重性をリセットできる**

段 2 は「全正式 candidate を family に含む」としつつ、失敗後は新 trial ID と alpha-spendingで再開可能とする。しかし親系列 ID、累積 alpha ledger、spending 関数、candidate 上限が未定義である。新 commit/new ID だけでは D126 が拒否した結果後の候補差し替えを無害化しない。
根拠: `output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:103-107,310-331`、`docs/decisions.md:6216-6219`

**成果物影響:** trial ごとに α=0.05 を再使用すれば偽の正例・certified artifact が増え、失敗系列を欠いた proof chain になる。

修正案: 最初の実走前に parent-series ID、全 candidate cap、alpha-spending関数、全 trial/attempt 双射を固定する。固定 family 方式と sequential family 方式を実質的な二択にする。

### **[real] P5 は correctness failure を session deletion で隠し、段2修正も reject まで閉じていない**

親 P5 は部分欠測なら session 全体を落とすため、arm 固有 timeout・verifier anomaly も消せる。段 2 は substantive failure と区別したが、complete session 不足を `indeterminate` に倒す記述が残り、規律2の「verifier anomaly は即 reject」を明示的に成立させていない。現行 `between_run_noise_floor()` も `None` を黙って除外する。
根拠: `output/insights/2026-08-03_t338-rf-statistical-design/brief.md:52-54`、`CLAUDE.md:67-71`、`orchestrator/calibrator/stability.py:117-126`、`output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:244-253,276-289`

**成果物影響:** correctness 不合格 arm が解析集合から消え、失敗 candidate が再試行経由で正例・certified 選択へ入る。

修正案: `correctness_reject` は candidate の terminal reject、outcome-blind infra failure だけ reserve replacement、性能欠測は事前規則どおり reject/indeterminate、と閉表化する。

### **[real] P1 の自動 unpaired fallback は fail-closed ではない**

親 P1 は pairing 不成立時に unpaired へ戻すが、同じデータについて二つの分析経路を用意する。負 covariance なら unpaired が保守的とは限らず、段 2 自身もこの fallback を拒否している。
根拠: `output/insights/2026-08-03_t338-rf-statistical-design/brief.md:37-41`、`output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:138-157`

**成果物影響:** pairing 判定や経路選択により正例受理が反転し、proof chain が一意でなくなる。

修正案: certification は `pairing invalid => indeterminate` のみ。事前登録済み unpaired protocol は非certification sensitivityとして別出力にする。

### **[real] Fieller の出力 schema は用意したのに、分類規則が全域を覆っていない**

段 2 は confidence set に `unbounded | disjoint` を許す一方、分類規則は「全体が0未満」「全体が(0,1)」「1を含む」「全体が1超」しかない。1を含まない disjoint set や複数境界に跨る unbounded set の status/acceptance が未定義である。
根拠: `output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:171-220`

**成果物影響:** 同じ Fieller set を材料レポートが `undefined`、`partial_recovery`、無分類のいずれにもでき、正例受理が非決定的になる。

修正案: bounded/unbounded/disjoint と 0/1 境界の全組合せについて、閉じた classification と certification mapping を定義する。

### **[real] D116 を RF へ自動拡張し、「追加凍結不要」としたのは未裁定**

D116 の決定文は Phase 8c 正式系列に限定される。一方 D126 が記録した RF 正例要件には「事前凍結 schedule」が含まれる。段 2 は D116 の一般化を新しい選択肢にせず、git ancestryだけで十分と断定した。しかも既存8cですら成果物への prereg commit binding は未実装である。
根拠: `docs/decisions.md:5494-5517`、`docs/decisions.md:6165-6167`、`docs/phase3-8c-preregistration.md:24-35`、`output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:310-329`

**成果物影響:** schedule の事前性を未実装の ancestry field だけで認定し、正例 artifact の proof chain が成立したように見える。

修正案: 「D116方式をRFにも拡張する」を明示的な裁定にし、prereg発効版・measurement checkout・submission receipt・ancestryを検査する consumer 実装を後続条件にする。

### **[refuted] docs-only で終えること自体は正しい**

D120 は正例 artifact ができるまで RF compute を land しないと明示し、D126 も識別可能性判定を実装していない。本 wave が authority none の裁定案だけを作り、bytes・gate・受理集合を動かさないのは既裁定どおりである。
根拠: `output/insights/2026-08-03_t338-rf-statistical-design/brief.md:3-10,25-31`、`docs/decisions.md:5743-5762`、`docs/decisions.md:6191-6195,6221-6224`

**成果物影響:** 現 wave では certified 選択、材料レポート、proof chain、正例受理集合はいずれも不変。

### **[refuted] P6 の Gate1 √2 問題を別件に保つ判断は正しい**

既存 `compare()` の √2 補正は既存レポートの比較可能性に触れる明示的保留である。RF が別名・別 consumer の confidence-margin方式を採る限り、現行 `noise_cv` を変更する必要はない。
根拠: `docs/archive/audit-2026-06-30.md:309-311`、`orchestrator/calibrator/stability.py:238-244`、`output/insights/2026-08-03_t338-rf-statistical-design/brief.md:55`、`output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:157-159`

**成果物影響:** 既存 Phase 2 report bytes と verdict の受理集合を不意に変更しない。

### **[refuted] 存在しない paired field を既存扱いしている、という攻撃は成立しない**

親 brief と段 2 は、既存 calibration が単一 arm の session mediansしか持たず、現存 probe に allocation/session 軸がないことを明記している。新 field は producer 要件として提示され、`noise_cv` とも別名化されている。
根拠: `output/insights/2026-08-03_t338-rf-statistical-design/brief.md:66-69`、`output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/throughput.tsv:1`、`output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/order.tsv:1`、`output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:165-169`

**成果物影響:** 現存 artifact は paired RF gate に誤受理されず、現時点の受理集合は不変。

### **[refuted] paired 化そのものが規律2違反、とは言えない**

correctness を先に独立 gate し、allocation単位、事前割付、raw covariance再計算、欠測非選択、pairing不成立時 indeterminateを機械強制できるなら、paired estimator は実際の誤差構造に合わせたものであり、correctness gate の緩和ではない。
根拠: `CLAUDE.md:67-71`、`output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:276-289`

**成果物影響:** 条件を実装できれば correctness の受理集合は変えず、性能識別だけを対応する推定量で行える。ただし現案は上記 consumer/validator 不在のため未達。

### **[refuted] 追補 B の「現存 probe は J=1」は正しい**

現存データの `rep` は一つのPBS job内の5反復であり、PBS receiptも Number of Jobs=1を示す。これを J=5 と数える余地はない。
根拠: `output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/order.tsv:1-31`、`output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/t139_positive_control_probe.pbs.e877859:3-13`、`output/insights/2026-08-03_t338-rf-statistical-design/brief-addendum.md:56-61`

**成果物影響:** 現存 probe から paired between-allocation floor は作れず、正例受理集合は不変。

## 判定

**NO-GO**

本パッケージは、ユーザーに択一として提示できる一つの設計へ閉じていない。最低でも D19/G12 の手続き、trial aggregation、`\delta_D` と estimand、family lineage、J/power/費用、欠測の terminal semantics、Layer3/eligibility consumer を組み込んだ package v2 が必要である。

pytest・build・benchmark・計測は実行していない。Pegasusログインノード上の静的読取りだけを行い、緑主張はしない。

## 総括

- 最重大: J=16別allocation案は現行G12 formal campaign契約と両立せず、追補Dにも実在する代替データがない。
- paired floor 採用はD19/roadmapの例外新設だが、明示的supersedeが裁定と原子的に結ばれていない。
- fresh marginal CV 0.11〜1.07%からpaired margin縮小を導く一般化は、covariance・環境・時間窓の証拠を欠く。
- eligibility authority、Layer3、selectorまでのconsumerがなく、提案gateは発火しない。
- trial固有paired統計をLayer3 calibration floorの第3 kindに足す設計はcandidate/contrastを識別できない。
- `pairing_valid`等が自己申告fieldのままで、D127型の恒真gateになる。
- 5点の外にestimand・primary endpoint・`\delta_D`等の未裁定項目が受理結果を支配する。
- J=16は選択したrandomization testとfamilyから導かれず、費用・reserve・停止上限も未裁定である。
- 新trial IDによる候補差し替えは、親系列alpha ledgerなしでは多重性をリセットする。
- P5はcorrectness failureをsession deletionで隠し得て、段2もterminal rejectまで閉じていない。
- P1の自動unpaired fallbackはfail-closedではなく、同じデータから分析経路を選べる。
- Fiellerのunbounded/disjoint confidence setに対する分類・受理規則が全域を覆っていない。
- D116のgit-ancestry方式をRFへ拡張する判断と、そのbinding consumerが未裁定・未実装である。