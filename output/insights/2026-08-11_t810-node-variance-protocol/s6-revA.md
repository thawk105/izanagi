# 段 6 レビュー A — 事前固定性

**判定: NO-GO。blocker 8 件、must-fix 1 件、nit 1 件。**

数値表の assurance は再現できましたが、主解析・validity・retry・binary identity・結果から運用判断への写像が固定されていません。現状では測定後に解析または解釈を選べます。

## 独立再計算

実 record は [g1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json) と [g2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json) を直接読んだ。

| 項目 | 再計算値 | 判定 |
|---|---:|---|
| g1 mean / CV | 3,918,457.8 / 1.1705838% | 一致 |
| g2 mean / CV | 3,848,941.0 / 1.2478966% | 一致 |
| 平均差 ÷ g1 | 1.7740857% | §0 の 1.774% と一致 |
| 平均差 ÷ g2 | 1.8061280% | 分母を変えると異なる |
| 平均差 ÷ 両平均の中点 | 1.7899635% | 分母を変えると異なる |
| `κ*=0.006/0.0124789655` | 0.4808091 | §4 と一致 |
| assurance 12/10 | 0.7926454 | 一致 |
| assurance 12/11、脱落後 | 0.8392202 / 0.7969723 | 一致 |
| assurance 12/12、脱落後 | 0.8768832 / 0.8385064 | 一致 |
| 臨界区間 | `144×3.47=499.68 node-s` | 約500 node-s は一致 |

一方、同じ式と制約を列挙すると `N=10,R=14` は full 0.860726、1 ノード脱落後 0.807814、総140反復であり、`12×12=144` より小さい。`N=14,R=10` も総140反復で条件を満たす。

## 所見

### 1. 主区間と assurance が同じ手続きを表していない

- **severity:** blocker
- **主張:** `τ_U` の構成が一意に定義されておらず、§4 の assurance は§5.1で宣言した主区間に対する assurance ではない。
- **根拠:** protocol §5.1 は「κのF反転とσ_eのχ²上限を組み合わせた保守的な同時被覆」とだけ書き、αの配分、`μ` の不確実性、負の分散成分の切捨て、下限の式を定義していない。各成分を片側95%にすれば同時被覆は少なくとも90%にしかならず、Bonferroni 95%なら各97.5%が必要である。一方、再現した§4の値は `F_0.05` だけを用いたκの判定であり、χ²上限やμを含まない。
- **成果物影響:** 実測後にCI方式・α配分・μの扱いを選べ、名目95%でない上限から「材料差を反証した」と宣言できる。
- **提案:** `τ_U`・`τ_L` の完全な式、α配分、μの下限、境界処理を固定する。bootstrap は resampling unit、B、seed、percentile/basic/BCa、log値からτへの変換を literal 化し、その最終手続きで assurance を再計算する。

### 2. §5.3 は排他でも網羅でもなく、validity と retry の literal が空である

- **severity:** blocker
- **主張:** validity 違反や attempt 選択を測定後に決められるため、段4 R6の「exact boolean predicate」は閉じていない。
- **根拠:** protocol §3.3–§3.4には開始時刻閾値、ready timeout、load閾値・回数・間隔・最大待ち、承認ホスト集合がない。§5.4の「最大 attempt 数」も値がない。§5.3の「全 validity 条件」は定義集合を参照せず、`σ̂_a=0` 行は他の結論行と重複し、`τ_U=τ*`・`τ_L=τ*` の等号も未定義である。repo inventory不一致、依存manifest不一致、外部receiptのschema違反がどのstatusになるかも表にない。
- **成果物影響:** 不利な attempt を後から invalid とし、好都合な attempt を「最初の有効 attempt」にできる。
- **提案:** `valid := P1 ∧ … ∧ Pn` の閉じた述語、`premeasurement_invalid / incomplete_after_release / valid` の全遷移、releaseを唯一の開始境界とする規則、最大attempt数、等号を含む全結論写像を一つの機械可読artifactへ固定する。job生成receiptは外部データとして厳格なfield集合・型・nonce/request ID・hashを検査し、shell sourceしないことも明記する。

### 3. `N=12,R=12` は「最小設計」ではなく、脱落目的は解析規則と矛盾する

- **severity:** blocker
- **主張:** §4の目的関数はスカラー化されておらず、採用点は同じ制約下の最小解でもないうえ、脱落後データを§5.4が全面禁止している。
- **根拠:** 独立列挙では `N=10,R=14` が脱落後 assurance 0.807814、総140反復で成立する。固定費が支配するという§4.2の説明を採れば、例えば固定費300秒では `N=5,R=54` の方が `N=12,R=12` より推定総node-sが小さい。さらに§5.4は12×12未満を全無効にし、脱落後11ノードで解析する経路を持たない。500 node-sは正しいが、固定費・生死確認・retryを含む総費用は最大attempt未定のため計算不能である。
- **成果物影響:** 根拠のない12ノード同時確保を authorizeし、脱落耐性を持たない解析へ「脱落耐性」を付与する。
- **提案:** 最大同時ノード数、総node-s、経過時間のどれを最小化するかを一つに固定する。11ノード解析を許すなら欠損規則とそのCIを事前登録し、許さないなら脱落assuranceを目的から削除する。

### 4. binary・環境契約・builder attempt が事前固定されていない

- **severity:** blocker
- **主張:** 「trace-disabled Silo」と「有効な環境契約」だけでは複数候補があり、builderやliveness後にbinaryを選び直せる。
- **根拠:** protocol §2には CCBench commit、genome、source token、compiler、flags、環境契約hashがない。実装の `build_v2` は [buildcache.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/orchestrator/campaign/buildcache.py:575) でcontractを必須にし、completion manifestへhashを記録するが、どのcontractを渡すかはcallerが選べる。現行g2の reviewed hashは [env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/orchestrator/campaign/env_contract.py:262) の `1346c20b…ad1c` である。§3.1はmanifestをbuilder後に固定するとしか書かず、builder再試行時にpreimage変更を禁じていない。
- **成果物影響:** liveness値や失敗を見た後にcommit・contract・toolchainを変え、好都合なbinaryだけを本走へ送れる。
- **提案:** commit `d706650c…`を使うならそれを含め、genome、trace=false、source token、compiler実体、flags、contract hashをbuilder前artifactへ固定する。同一preimageの再試行上限と、preimage変更は新protocol扱いという規則を置く。

### 5. 測定結果から downstream 判断への写像がない

- **severity:** blocker
- **主張:** §5.3の三結論からfan-out可否とT-139感度表へ進む規則がなく、結果を見て用途を選べる。
- **根拠:** §7はfan-outの「可否判断」を変えてよいとするが、`τ_U<τ*`、材料差支持、未決の各場合に何を許可・禁止するかを書いていない。§1.3のT-139式は `τ²·E[回復量]² の程度` に留まり、「説明割合」の分母、`E`の点推定/区間、τの点推定/上限、共通乗数との独立性を固定していない。また§1.3の「唯一の用途」は§7の二用途と矛盾する。
- **成果物影響:** 小さい結果ならfan-out解禁、大きい結果なら限定的感度表だけ、という事後解釈が可能になる。
- **提案:** 結論状態×許可判断の全対応表を作る。T-139は完全な式と入力を固定するか、単一armでは識別不能として用途から削除する。

### 6. drift が結論方向を歪めないという主張は誤りである

- **severity:** blocker
- **主張:** `τ`の定義がσ_eを分母に持たなくても、そのANOVA推定量は`MS_E`を使うため、未モデル化driftはσ̂_aを下方へ歪め得る。
- **根拠:** 実record再計算でbnode048は相関 −0.658951、傾き −10,453.6 tps/rep、初回→最終 −2.605%。一元配置推定では通常 `σ̂_a²=(MS_A−MS_E)/R` なので、全ノードに共通するround driftが`MS_E`へ入るとσ̂_a²を押し下げる。protocol §5.2の「結論の向きは歪まない」はestimandとestimatorを混同している。
- **成果物影響:** 実在するノード差を過小評価し、誤って`τ_U<τ*`へ入る可能性がある。
- **提案:** 反復roundを同期し、round固定効果を含む事前固定モデルへ変更する。代替として、drift時に主結論を停止する閾値か、driftに対して被覆を確認した主手法を先に固定する。

### 7. §9 は現在は停止表示だが、将来の実効 authorization gateとして閉じていない

- **severity:** blocker
- **主張:** 未実装である現時点では走れないが、§9の要件を「実装済み」と自己申告するだけで本走へ進める余地がある。
- **根拠:** §9項7が機械可読化を要求するのは§2・§4・§5.3・§5.4だけで、§3のthreshold/timeout、§5.1のCI、§5.2のbootstrap、§6.2のpresence matrix、binary preimageを含まない。誰が「閉じた」と判定するか、validator/testのexpected set、liveness成功receipt、別の走行承認tokenもない。
- **成果物影響:** 形式的に7項目を実装しただけで12ノード投入を正当化でき、未固定の解析・validityを残したまま資源を消費する。
- **提案:** freeze済みprotocol digest、実装acceptance manifest、全validator結果、成功liveness receipt、予算receipt、独立した人間のrun authorization IDを必要条件にする。本文書のlandだけではbuilder・liveness・本走のいずれもauthorizeしないと分けて書く。

### 8. runbookの「無条件でよい」が直後の但し書きを無効化している

- **severity:** blocker
- **主張:** 並行投入節はjob内比較fan-outを「無条件」としながら、同じ箇所でnode効果が複合量に残ると認めており、運用規則が自己矛盾している。
- **根拠:** runbook「ノード間の性能差は未測定」節は「jobの内側で比較が閉じているfan-outは無条件でよい」「nodeは共通因子として相殺」とした直後に、加法効果は水準を含む量に残り、乗数効果は差を定数倍すると追記している。これはT-139の`劣化幅−κ·stock`型で実際に残る。
- **成果物影響:** 「無条件」の一文だけでfan-outし、nodeを設計因子に持たない複合量をjob間集約できてしまう。
- **提案:** 「無条件」を削除し、estimandが仮定したnode作用に対して不変である場合だけ許すと書く。差・比・水準混合量ごとの判定表を置き、job間集約はprotocolの明示写像へ送る。

### 9. `τ*=0.6%` の根拠は数値上「半分」ではない

- **severity:** must-fix
- **主張:** 0.6%を実測1.2478966%の「半分」と断定するのは不正確である。
- **根拠:** 実際の半分は0.6239483%で、0.6%はその96.16%。また「どの判断も変えない」を裏付ける既存の判定marginは提示されていない。
- **成果物影響:** materialityが運用損失から導かれた値ではなく、丸めた経験値であることを隠す。
- **提案:** 「約半分へ保守的に丸めた人間の価値判断」と書き、判断marginとの対応がない限り「どの判断も変えない」を削除する。

### 10. §0の期間と百分率の定義が曖昧である

- **severity:** nit
- **主張:** 1.774%の分母と「19日」の数え方が明記されていない。
- **根拠:** 1.7740857%はg1平均を分母にした場合だけ一致し、対称percent differenceは1.7899635%。`submit_epoch`差は1,578,555秒=18.2703日で、日付差だけなら19日である。
- **成果物影響:** 直接の判定差ではないが、後続の再計算で別値が生じる。
- **提案:** 「g1平均比」と「UTC日付差19日／実経過18.27日」を明記する。

## 段3 blocker 対応表

| 段3所見 | 状態 | 確認結果 |
|---|---|---|
| A-1 F-1をmaterialityへ転用 | **partial** | 1.774%からの逆算は削除されたが、0.6%=半分という根拠が不正確で運用marginとの接続もない。 |
| A-2 単一armはT-139を支えない | **partial** | 共通乗数モデルへscope限定したが、説明割合の式・入力・上限構成が未固定。親のX1は結論を強くしすぎている。 |
| A-3 κはmaterial node varianceでない | **closed** | τを主、κ/ICCを副次へ降格した。 |
| A-4 exact CIはexactでない | **partial** | working modelとdriftは明記したが、主CI・bootstrap未定義で、driftが結論方向を歪めないという新しい誤りが入った。 |
| A-5 N/Rは規模最適化でない | **partial** | 12/12へ変更しただけで、10/14という小さい解を落とし、脱落目的と欠損禁止が矛盾。 |
| A-6 事後分岐が残る | **partial** | release後retry禁止と最初のvalid attemptは書いたが、validity、最大attempt、CI、結論写像が未固定。 |
| B-1 build_v2経路・contract hash | **partial** | legacy拒否は要件化したが、使用contract hashとsource preimageがliteralでない。 |
| B-2 runtime identity | **closed** | 依存名・path・hash、module、`LD_LIBRARY_PATH`、`/scr`検査とrelease token束縛を要件化。 |
| B-3 group barrier/revocation | **closed** | §3.3と§9にbarrier、cancel marker、直前再確認、exact verifierを実施前要件として記載。 |
| B-5 `--certify`機械禁止 | **closed** | capability遮断とargv allowlistを実施前要件として記載。 |
| B-6 repo全体の非流入 | **closed** | repo forbidden、ignored file inventory、wildcard namespace deny、exact setを要件化。 |
| B-7 repo外root policy | **partial** | policy注入は要求したが、root literal、owner/mode、mount identity、retentionが未固定。 |
| B-8 B系並走ガード | **closed** | exact parser、unknown拒否、A優先receipt、競合時withdrawal、毎回再確認を要件化。 |
| B-9 budget admission | **partial** | admission自体は要求したが、換算式、固定費、retry上限、必要残高の比較式がない。 |

段4でscope外とした実装要件については、B-3/B-5/B-6/B-8は文書上の要件として書けている。B-4のwrapperはthreshold literalがなく、B-9の予算換算器も入力式がないためpartialである。B-10相当の`qsub -o/-e` exact pathと失敗状態別presence matrixも、実装可能なliteralまでは閉じていない。

絶対規律1についてtrace-disabledと全nodeでのtrace記号検査は要求されている。規律4についてレコード数1,000,000は実recordの`working_set/L3≈4.93×`という下限基準に一致するが、N/Rの最小性が破れている。規律6についてjob receiptを「閉じたschema」と呼ぶだけでfield・型・nonce束縛が未定義であり、所見2の修正が必要である。

## 総括

**NO-GO。blocker 8 件。**

攻撃が最も深く届いたのは、段4 R6が「exactに閉じる」と裁定した面である。実際には主CI、lower bound、bootstrap、validity、最大attempt、binary preimage、fan-out/T-139への結論写像が未固定であり、§5.3も排他・網羅になっていない。現在は未実装なので即時走行できないが、§9を満たしたという形式だけで将来の12ノード投入を安全にauthorizeできる状態ではない。