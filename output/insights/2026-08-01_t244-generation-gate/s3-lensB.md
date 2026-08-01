## 総括

- **[致命]** S1 は `--max-generations` の値しか塞がず、同じ trial/config と別 `--run-root` の 1-generation build を反復すれば shared campaign state 上で最大10 iterationの適応探索を再構成できる。
- **[致命]** 候補 B の planner-only 分離は成立しない。`direction×magnitude` の9記号は `log2(9)=3.170 bit/世代` を coder へ運び、4-class=2 bit を一世代で符号化できる。
- **[高]** 既存 `loop_state.json` は field 名だけ閉じ、`direction/magnitude/result` の値を検証しないため、任意の機序・指示文字列を planner/coder へ流せる。
- **[高]** `delta_pct≡None` は planner 全体の性能リーク防壁ではない。絶対 throughput と LLC miss/IPC が別 field で渡り、9記号を世代間メモリにすれば粗い差分を復元できる。
- **[高]** 段2の A〜D は裁定材料として不足する。A は停止策、C は padding で匿名化崩壊、D は禁止経路の直結であり、機械的な safety-constraint 還流や auditor 専用経路が欠落している。

## 所見

以下でいう「成果物への影響」は、8c 自体が直ちに正式 certified selection を更新するという意味ではない。8c report は `scientific_claim=False` である (`orchestrator/campaign/p3_autonomous_workload_trial.py:579-592`, `:972-980`)。直接変わるのは campaign WAL の受理候補、outer report、proposal、attempt journal であり、それを後続の正式系列が材料採用した場合に certified selection / 材料レポートへ波及する。

### B-01 — S1 は cross-generation 不変条件を機械化しない

- **何が壊れるか:** `--max-generations 1` を複数 invocation に分割すれば、各 invocation は S1 を通過したまま過去 whiteboard を読み、適応探索を継続できる。S1 が守るのは「1 CLI invocation 内の generation 数」であって「campaign 全体で過去 feedback を読まないこと」ではない。
- **file:line の根拠:** campaign identity は config 内容と `trial` の hash (`orchestrator/campaign/ident.py:76-103`)。8c config は `trial_id` と `generation_budget` を含む (`orchestrator/campaign/p3_autonomous_workload_trial.py:400-429`)。build 時の layout は `run_root` でなく共通 `output/campaigns/<id>` (`:631-635`)。fresh 検査は外側 `run_root` だけ (`:869-876`) で、planner 前に `_whiteboard()` が既存 state を読む (`:474-476`, `:655-676`)。D106 も同じ経路を既知残余として明記する (`docs/decisions.md:4876-4879`)。
- **成果物への影響:** 2回目の outer report は `cells[].generations[0].generation == 1` のまま、`harness.iteration == 2` 以上になりうる (`p3_autonomous_workload_trial.py:659`, `:783-804`; driver の iteration は `p3_s4_loop_trigger_gating.py:487-518`)。`campaign_root` は同じ (`p3_autonomous_workload_trial.py:641-642`) で、共有 WAL に新しい certified COMMIT が入りうる。planner/coder の payload SHA、proposal、report の `variant/outcome/fitness_tps` が変わる。
- **判定:** **must-fix**。freshness/origin gate をS1へ含めるか、「S1は flag 禁止だけで feedback 禁止ではない」と主張を狭めてユーザー裁定へ返す必要がある。

### B-02 — 候補 B の recipient separation は情報フロー分離になっていない

- **何が壊れるか:** planner justification の文字列自体は coder へ転送されないが、planner が `prior_failure_v1.class` を `direction/magnitude` に符号化できる。coder はその9記号を直接受けるため、4-class の機序分類が一世代で届く。
- **file:line の根拠:** planner 出力の値域は direction 3値・magnitude 3値 (`p3_autonomous_workload_trial.py:207-232`)。coder 射影は axis/direction/magnitude (`:694-711`)。D43 と coder contract はこの組を機序でなく中立な抽象信号として扱う (`docs/decisions.md:1439-1442`; `.claude/agents/coder-v4-autonomous-trigger-gating.md:30-34`)。D45 は自然文 lint を防壁にする案を明示的に却下している (`docs/decisions.md:1565-1568`)。
- **成果物への影響:** coder の `implementation` が class に依存し、proposal bytes (`p3_autonomous_workload_trial.py:774-782`)、attempt journal の input SHA/parsed output (`:527-570`)、campaign の reject/certified 集合、report の harness result (`:802-804`) が変わる。verifier が不完全なら、class を勾配として blind spot を通る variant が certified 候補へ入る。
- **判定:** **must-fix**。候補 B を「第一候補」とする結論は撤回対象。no-echo prompt、canary、recipient key の不在テストではこの意味チャネルを検出できない。

### B-03 — 既存 whiteboard は許可 field の値を使った無制限リーク経路を持つ

- **何が壊れるか:** `loop_state.json` の `direction`、`magnitude`、`result` に任意の長文、機序、prompt injection を入れられる。field 名が5個でも値域が閉じていないため、D39の「機序経路を型で排除」は外部 checkpoint に対して成立しない。
- **file:line の根拠:** `state_from_dict()` 自身が checkpoint を信頼境界外と宣言する (`orchestrator/campaign/p3_s4_loop.py:371-381`) が、検査は未知 field と `delta_pct` だけで、残りを無検証で格納する (`:389-404`)。`whiteboard_for_planner()` は値をそのまま射影する (`:273-286`)。8c はそれを planner/coder 双方へ渡す (`p3_autonomous_workload_trial.py:666-676`, `:694-711`)。campaign identity の照合は roles 呼び出し後の `run_one_iteration()` 内まで来ない (`p3_s4_loop_trigger_gating.py:402-404`)。
- **成果物への影響:** tampered/stale state が role payload と input SHAを変え、planner/coder出力、partial/complete status、proposal、共有 WAL の受理 variantを変える。単なる report 表示漏れではなく variant 生成前の入力汚染である。
- **判定:** **must-fix**。少なくとも exact enum/type/range、entry count、iteration整合、campaign/run originを roles 呼び出し前に検査すべきである。本 wave scope外でも real。

### B-04 — 絶対性能値は許可済みだが、`delta_pct` 防壁を全体保証として使えない

- **何が壊れるか:** planner/coder は直前の絶対 throughput、LLC miss、IPC 等を受ける。fresh context 単体では過去 throughput を直接持たないが、planner は前世代値を9記号へ量子化して whiteboard に残し、次世代で現在値と比較できる。候補 B/D の失敗 class と結合すると「性能勾配＋正しさ gate の段階分類」という強い oracle になる。
- **file:line の根拠:** metrics は outcome から抽出され (`p3_autonomous_workload_trial.py:479-501`)、generation 後に更新 (`:783-804`)、次 planner の `current_perf/leading_indicators` と coder の `baseline` に入る (`:646-711`)。D39の決定3は whiteboard の機序・値経路を閉じる局所契約 (`docs/decisions.md:1102-1108`)。一方、planner-v4 は current throughput/LI を明示入力とし (`.claude/agents/planner-v4.md:17-45`)、coder-v4 と D51 も「本 campaign 自身の baseline」は許可する (`.claude/agents/coder-v4-autonomous-trigger-gating.md:24-29`, `:50-58`; `docs/decisions.md:1957-1962`)。
- **成果物への影響:** 現行裁定上、coder baseline 自体は違反ではない。しかし multi-generation では proposal と certified/rejected 分布を変える live reward である。S2候補の漏洩量を「4-classの2 bitだけ」と評価すると過小になる。
- **判定:** **must-fix（裁定上）**。既存 contract 違反とは断定しないが、`delta_pct≡None` を「plannerへ性能値を渡さない保証」と説明してはならない。失敗 class と性能値を同時配信するかを明示裁定すべきである。

付随する real defect として、`cache_miss_rate_pct` と `abort_rate_pct` には 0..1 の率がそのまま入る (`p3_autonomous_workload_trial.py:497-500`, `:670-673`)。元データの LLC miss は 0..1 と定義される (`orchestrator/calibrator/model.py:38-44`, `:86-98`) 一方、planner例は percent 表記 (`.claude/agents/planner-v4.md:32-40`) である。100倍の意味ずれにより proposal と台帳受理 variant が変わりうるため、これも **must-fix before multi-generation**。

### B-05 — S1 は必要だが、規律3の解ではない

- **何が壊れるか:** 機械 gate を入れない現状では、禁止値2がCLI既定であり、運転者が flag を省くだけで禁止運転へ入る。一方、gateを入れて1世代へ固定しても「なぜ壊れたかを次の variant へ使う」規律3は実装されない。
- **file:line の根拠:** 現行CLI既定値は2 (`p3_autonomous_workload_trial.py:1017`)、programmatic経路は1..10を受理 (`:857-860`)。runbookは禁止を宣言するだけ (`docs/phase3-s8c-autonomous-trial-runbook.md:98-101`, `:158-164`)。F9は発火しない検査にpositive controlを要求し (`docs/failures.md:104-110`)、F21は設定/単体検査とlive経路を同一視した事故を記録する (`:263-273`)。
- **成果物への影響:** 機械 gate は `>=2` invocation を report/WAL生成前に拒否し、受理集合を安全側へ狭める。規律2を緩めず、規律3も直接緩めない。ただし正式H1/H2の生成・report・材料台帳は引き続き作れず、T-244の本体は未完のまま。
- **判定:** **must-fix**。S1実装は採用してよいが、「T-244解決」「規律3還流を閉じた」と記録してはならない。

### B-06 — 段2の裁定パッケージは再検討可能な形になっていない

- **何が壊れるか:** 候補Bは間接チャネルを認識しながら第一候補とし、最終防壁をprompt文面に置く (`s2-plan.md:210-235`)。候補Cは安全性でなく「短いtrialでは役に立たない」を主な降格理由とする (`:268-287`)。feedback fieldをreportへ残すかも任意扱い (`:214-217`) で、後からplanner判断の原因を再構成できない。
- **file:line の根拠:** D45は自然文検査を唯一防壁にしないと決定済み (`docs/decisions.md:1565-1568`)。規律3の赤構造は現在 critic digest へ保存される (`orchestrator/critic/digest.py:81-105`, `:544-680`) が、候補B/Cでは公開分類のproducer、iteration、variant、source reasonへの束縛が定義されていない。
- **成果物への影響:** ユーザーがBを選んでも、後日のdecision台帳から「何bitを誰へ公開し、どの残余oracleを受容したか」を再検討できない。reportのpayload hashだけでは分類内容を復元できず、proof chainが説明不能になる。
- **判定:** **must-fix**。recipient matrix、情報量、producer trust、origin binding、query budget、report schema、不採用理由を裁定項目へ加える必要がある。

## 1 generation 還流の判定

**結論:** 「fresh campaign の単一 invocation」という限定なら D106 残余1が正しい。実際の build 経路全体について「1 generationなら還流ゼロ」と一般化すると誤り。ただしこれは **D106残余3に逐語的に記録済みの既知事実**であり、段4で新事実として裁定を失効させてはならない。

経路は次のとおり。

1. `_campaign_for()` は `trial_id`、workload、generation budget等を configへ含める (`p3_autonomous_workload_trial.py:400-429`)。
2. 同じ trial/configなら `campaign_id` は同じになる (`orchestrator/campaign/ident.py:76-103`)。
3. `--run-root` のfresh検査は outer artifact rootだけ (`p3_autonomous_workload_trial.py:869-876`)。
4. build時の campaign root は `--run-root` と無関係な共有 layout (`:631-635`)。
5. generation 1 の plannerを呼ぶ前に `_whiteboard()` がその共有rootの `loop_state.json` を読む (`:474-476`, `:666-676`; `p3_s4_loop.py:421-427`)。
6. driverも同じstateをloadし、既存iterationを継続する (`p3_s4_loop_trigger_gating.py:483-518`)。

したがって、次の組合せになる。

- fresh `run_root` + `--no-build`: campaign rootも新しい `run_root/campaigns/...` 配下なので、通常は過去feedbackなし。
- build + 新しい `trial_id/config`: campaign IDが変わるため、通常は過去feedbackなし。
- build + 同じ `trial_id/config` + 別 `--run-root`: 過去whiteboardがgeneration 1へ届く。S1を通る1-generation invocationを連結できる。

D106は残余1で「1 generationなら本欠陥は発火しない」 (`docs/decisions.md:4854-4867`) としつつ、直後の残余3で別run-rootから旧stateを読むと明記する (`:4876-4879`)。よってこれは新事実ではなく、残余1の射程を残余3が限定している構造である。

段4で必要なのは「D106を新事実で失効」ではなく、次のどちらかの裁定である。

- S1を campaign freshness / total iteration まで拡張する。
- S1は `>=2` flagだけの部分防壁と明記し、残余3経路を許容したままT-244を未完で残す。

## S2 候補への攻撃

### 候補 A — 現状維持、1 generation/cell

Aは規律3の設計解ではない。単一attemptでは「次のvariant」がないため欠陥が発火しないだけであり、規律3の「失敗理由を次手入力にする」能力を実装していない。D106が「直せば済む欠陥でなく設計択一」としたのは、critic→generatorを単純接続するとD39/D45の禁止経路を再開するためである (`docs/decisions.md:4854-4867`)。

提示された最悪シナリオより悪い攻撃は、**複数の1-generation build runを同一campaignへ連結すること**である。毎回別 `--run-root`、同じtrial/configで起動すれば、S1を一度も破らず最大10 iterationのoracle探索を再構成できる (`p3_s4_loop.py:79-83`)。現行 `result` だけでも accept/fail/rejected の最大 `log2(3)=1.585 bit/attempt` がある。

したがってAは「停止・封じ込め候補」としては残せるが、「S2設計候補」と同列に置いてはならない。

### 候補 B — planner-only の4-class

#### justification 経路

実コードでは plannerの `justification/uncertainty` は coder payloadへ転送されない (`p3_autonomous_workload_trial.py:702-708`)。したがって「文字列がそのまま coderへ届く」という攻撃は **refuted**。

しかし意味チャネルは閉じていない。

- direction: 3値
- magnitude: 3値
- axis: 固定1値
- coderへ届く記号数: `3×3=9`
- 容量: `log2(9)=3.169925 bit/世代`
- failure class: 4値=`2 bit`

例えば4 classを `(increase,small)`, `(increase,medium)`, `(decrease,small)`, `(decrease,medium)` に割り当てれば一世代で運べ、5記号余る。planner contractの「echoしない」はこの符号化を止めない。

#### accept/reject oracle

gate predicateの enum は8値で、`kUnset` は必ずtrue (`.claude/agents/coder-v4-autonomous-trigger-gating.md:82-103`)。残り7要因ごとにtrue/falseを選ぶ意味空間は最大 `2^7=128` predicates、識別情報量は7 bitである。

- binary accept/rejectが任意の二分探索として働く条件なら、7 evaluated generationsで識別し、8世代目で利用できる。
- 「危険要因が7個中1個」の単一culprit/group-test仮定なら `ceil(log2 7)=3` probe、4世代目で利用できる。
- 4-classが理想的な4分岐oracleとして働けば、理論下限は `ceil(log4 128)=4` evaluated generations、5世代目で利用できる。
- 一般の非単調 verifier では二分探索は保証されず、最悪128点列挙になる。この前提を明示せず「二分探索可能/不可能」と断定するのも不正確である。

現行 `MAX_ITER=10` には、7-bit one-factor探索と8世代目の利用が収まる。収束停止はdirection/magnitudeを交互に変えれば避けられる。

#### `null` bit

fresh・同一runで、`prior_failure_v1` が最新 `whiteboard.result` から決定論的に導出されるなら、`null/non-null` は既存の success/fail/rejected と generation番号の関数であり、条件付き情報量は **0 bit、重複**である。

ただし現実には whiteboardがrun originを持たず、dry-passはwhiteboard entryを追加しない (`p3_s4_loop_trigger_gating.py:411-412`)。freshness/origin/attempt bindingなしでは、`null/non-null` が「今回runでfailureが生じたか」を識別する純増1 bitになりうる。候補Bはこの等価性を機械assertしていない。

また既存 `result=fail` に対する追加分類が correctness/liveness/infrastructure の3値なら、最悪の純増は `log2(3)=1.585 bit` である。

**判定:** Bは現在の形では不採用。採るなら「漏れない」ではなく「最大何bitの漏れを承認し、何queryまで許すか」という裁定に変える必要がある。

### 候補 C — 3件window集約

固定windowでも、plannerがwindowの構成要素を選べる限り匿名化は成立しない。具体手順は次のとおり。

1. planner/coderがgeneration番号と9記号のcodebookを共有する。
2. windowの最初の2 attemptsで既知class `P=candidate-policy` を強制する。例えば禁止識別子を含む1行を出せば pre-audit/syntax contract が決定論的にrejectする (`p3_autonomous_workload_trial.py:157-162`, `:729-746`; `p3_s4_loop_trigger_gating.py:318-324`)。
3. 3件目だけ対象predicate `T` を試す。
4. `classes_present={P}` なら、既存whiteboard.resultと組み合わせて `T` が success またはPかを判別する。`{P,X}` なら `T=X` が一意に復元される。
5. 次windowでは境界位置をずらし、別padding classを使えば曖昧さも消せる。
6. 復元したclassを9記号でcoderへ転送する。

4 classの集合は最大16通り=`4 bit/window` を表す。window size 3でも、既知paddingを使えば対象1件の2-bit classを完全復元できる。これは集合差分による近似でなく、一windowでの一対一復元である。

さらにbufferをouter runローカルに置けばrestartで境界を選び直せ、campaign stateへ永続化すればAと同じ別run-root連結が使える。どちらでも origin binding と trusted window composition が必要である。

**判定:** 現案は不採用。plannerがwindow構成を制御できない trusted scheduler、padding耐性、campaign-global境界、開示budgetがなければBより遅いだけである。

### 候補 D — planner/coder双方へ4-class

Dは「具体reasonを削ったから安全」ではない。coderが直接、

- candidate-policy → syntax/diff/auditor面を変更
- correctness → verifierを通る方向を探索
- liveness → timeout/commit枯渇を避ける
- infrastructure →候補を維持して再試行

と分類できる。さらに absolute throughput/baselineも同時に見えるため、「性能を上げつつどのgate段で落ちたか」という多目的rewardになる。これはD39が排除した勝ち筋逆算経路そのものである。

意味的な逆算をexact-key、canary、schema testで止めることはできない。prompt規律は規律6上、外部role出力を信頼した唯一防壁になれない。

**判定:** 不採用理由は確定可能。比較候補として残すなら「採らない negative control」と明示すべきである。

## 段 2 プランが挙げていない設計軸

### 1. trusted machine が failure を safety constraint に変換する

最も重要な欠落である。failure reasonをplanner/coderへlabelとして渡さず、trusted orchestratorが閉じた単調制約へ変換し、次候補の admissible setを機械的に狭める。

例:

- `must_backoff_on={...}`
- `forbid_read={...}`
- `required_invariant={...}`
- `candidate must refine previous safe predicate`

generatorは理由を見ず、制約違反候補が機械的に生成/受理されない。規律3のreasonは次variant生成の制約入力になり、規律2のgate探索用labelは公開しない。制約言語、単調性、positive control、受理集合変更は新Dで凍結する必要がある。

### 2. failureを post-run auditorだけへ戻す

auditorへ構造化anomalyを返し、auditorは次variantのコードを自由生成せず、機械検証可能な safety obligation / vetoだけを返す。planner/coderはgeneric rejectしか受けない。

これは有望だが、auditorの自由文をそのままgeneratorへ渡せばB/Dと同じになる。auditor出力は外部データとしてexact schemaとtrusted enforcementで拘束しなければならない。

### 3. critic側でdeclassifyする

criticは既にraw digestを受ける (`p3_autonomous_workload_trial.py:806-818`)。criticへ4-classを出させるだけでは安全にならない。critic自身が4値を2-bit covert channelとして使えるためである。

採用可能なのは、authoritative structured WALから機械的にclassを再計算し、critic出力と一致検査する形だけである。それでもclass公開によるoracleは残るため、単なるproducer信頼の問題と情報公開の問題を分ける必要がある。

### 4. 別roleを挟む

別roleは、それだけではsecurity boundaryではない。同じ4値を返すdeclassifier/repairerは同じチャネルを再現する。

成立しうるのは、

- 性能値を一切受けない
- free-form codeを返さない
- safety-monotoneな閉じた操作だけ返す
- trusted machineが操作を再検証する
- planner/coderへ理由を転送しない

という「制約生成role」である。

### 5. verifier feedback前に候補batchを凍結する

候補集合を事前にcommitし、そのbatchの全候補についてcorrectnessを評価してから性能を見る。failure reasonは次batchの安全制約更新にだけ使う。adaptive one-query-at-a-time oracleを弱められる。

batch境界、全件報告、候補追加禁止、失敗理由と性能の同時開示禁止が必要である。

### 6. campaign-global disclosure/query budget

`--max-generations` ではなくcampaign stateの総iteration、公開class数、window数を束縛する。別run-rootやprogrammatic callに分割してもbudgetを回復させない。A/B/Cすべてに必要な横断軸である。

## 裁定パッケージ候補

段4へ返すべき裁定は次の形である。

1. **S1の射程**

   - 推奨: CLI/direct `run_trial()` 共通validatorに加え、generation 1 planner前のcampaign freshness/origin gateをS1へ含める。
   - 次善: `>=2` flagだけ拒否し、「別run-root連結は残る部分防壁」と明記する。
   - 禁止: S1だけで「cross-generation還流を機械的に禁止した」「T-244をclose」と記録する。

2. **S2の当面状態**

   - Aを「設計候補」でなく「封じ込め」として採用し、T-244本体は未完のまま残す。
   - Bは情報開示budgetとoracle threat modelがないため採用しない。
   - Cはpadding攻撃により採用しない。
   - DはD39禁止経路を直結するため採用しない。
   - 次設計waveでは trusted safety-constraint mediator + auditor-only laneを第一候補にする。

3. **既存scope外だが real**

   - `state_from_dict()` の direction/magnitude/result exact enum/type検査と、roles呼出し前のorigin/identity検査。
   - `current_perf`、`leading_indicators`、coder baselineのrecipient matrixと世代間情報量を新Dで明示。
   - `*_pct` の0..1/0..100単位契約修正。
   - failure feedbackを導入するなら、class、source variant、iteration、authoritative reason category、declassifier versionをreport/proof chainへ必須保存する。

4. **後から再検討できる不採用理由**

   各候補について最低限、次をdecisionへ残す必要がある。

   - 誰がどのfieldを見るか
   - 一世代/一window当たりの最大bit数
   - accept/reject queryの総予算
   - producerがtrusted machineか外部roleか
   - run/campaign origin binding
   - 正式report/WALへ残す参照
   - 受容する残余と、不採用案を再開できる条件

現行 `s2-plan.md` のコスト見積りとprompt文面だけでは、この水準を満たさない。

## 確認できなかったこと

- 必須指定された8資料はすべて読了できた。読めなかった指定ファイルはない。
- `pegasus02` login nodeかつread-only条件のため、pytest、CLI実走、build、campaign生成は行っていない。テスト緑は主張しない。
- 現在ディスク上に、攻撃へ利用できる特定の8c `loop_state.json` が実在するかは調べていない。経路の成立はコードとD106残余3による静的確認である。
- 9記号の符号化、padding攻撃、oracle世代数は情報理論上・コード値域上の上限評価であり、実LLMが自発的にそのcodebookを使用することは実測していない。規律2の脅威モデル上は「可能なら攻撃に使われる」として扱うべきである。