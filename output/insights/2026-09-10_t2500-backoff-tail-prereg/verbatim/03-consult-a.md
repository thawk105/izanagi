## 所見

### [real] [must-fix] 4 桁量子化を無視した区間は飽和を宣言しやすい

根拠: 停止式は rep の abort 率から標本 sd、`se`、`qL` を直接作る (`/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/plan.md:122-143`)。しかし実 report の abort 率は 4 桁に量子化され、read-heavy 9999 µs は `[0.0073,0.0074,0.0074,0.0074,0.0074]` である (`/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/b10-backoff-grid-20260908T193601Z-2540578-read-heavy/campaigns/t2418-backoff-static-explore-v1-silo-read-heavy-sweep-a3c44399/reports/t2418-backoff-static-explore-read-heavy.json:1`)。最終 2 区間は短いため (`plan.md:42-45`)、同じ `0.0074` に丸められる真値 0.007449→0.007351 でも、倍増換算の低下は約 7.9%になる。登録式はこれを `qhat=0, se=0, U=0` 相当にして 5%基準を通し得る。これは「測れていない」を「飽和」とする向きの誤りで、規律 2 と 3 に触れる。

成果物影響: workload ごとの飽和位置、bracket、集約 verdict が非飽和から飽和へ反転し得る。

提案: formal schema に rep ごとの丸め前 numerator・denominatorまたは十分な精度の raw abort 率を必須化し、それから解析値を再導出する。取得不能なら、丸め区間を `qL` に伝播する保守的手続きを本走前に再登録する。

### [real] [must-fix] 正値かつゼロ分散の cell 対で `nu` が未定義になる

根拠: `v_i=cv_i^2/5` とした上で、`nu=(v_i+v_prev)^2/(v_i^2/4+v_prev^2/4)` とする (`plan.md:124-140`, `plan.md:491-498`)。隣接両 cell が正値 `[0.0074]*5` なら両方の `v=0` で `nu=0/0` になる。この入力は有限・範囲内・5 rep 完備・CV 2%未満なので、現行の失敗条件を通る (`plan.md:523-547`)。特例は「両 cell が全ゼロ」だけで、正値ゼロ分散は閉じていない (`plan.md:157-162`, `plan.md:500-504`)。

成果物影響: 有効 cohort なのに `qL`、`U`、飽和位置、allowed verdict のいずれも生成できない。

提案: 量子化問題を raw counts で解消した上で、なお正値ゼロ分散が起きた場合の fail-closed 規則を明記する。単に `se=0` として通すのは偽飽和を作るため不可。

### [real] [must-fix] 探索の最大 CV 0.65%は throughput CVであり、abort 閾値の根拠ではない

根拠: plan は最大 CV 0.65%を abort 飽和幅 5%と CV gate 2%の根拠に使う (`plan.md:153-155`)。機械 spec も metric 無指定の `maximum_reported_cv` とする (`plan.md:251`)。現物では `cv` は `bench.get("cv")` から入り (`orchestrator/campaign/backoff_extended_sweep.py:1088-1106`)、read-heavy 4000 µs の report 値 0.00220348 は throughput reps の CVと一致する一方、abort reps の CVは約 0.00375179である。同様に静的 9 cell の最大は throughput 0.00650836、abort 0.00615149だった。後者も量子化に支配されるため精度根拠にはできない。

成果物影響: exploration disclosure の field 意味と、5%・2%を正当化する参照が変わる。閾値を維持するなら別根拠が必要になる。

提案: `maximum_reported_throughput_cv` と `maximum_recomputed_abort_cv_from_quantized_rates` に分離し、後者を検出精度の根拠に使わないと明記する。

### [real] [must-fix] 前向きなのは formal cohort に対する規則だけである

根拠: T-2418 一次資料は、探索時には格子も停止基準も凍結しておらず、結果は「観察であって判定ではない」と限定する (`t2418-explore-README.md:193-226`)。plan は格子と5%幅を探索後に選んだこと自体は開示する (`plan.md:68`, `plan.md:153`, `plan.md:255`)。一方、表題計画は無限定に「docs-only の前向き固定」とし (`plan.md:14-15`)、spec は探索に対して `observed_saturation_status` という判定風の field を置く (`plan.md:251-255`)。先例は「probe後の改訂は事前登録ではない」「前向きなのは未観測の throughput に対する規則だけ」と逐語で限定している (`docs/b10-backoff-shape-preregistration.md:41-51`, `docs/b10-backoff-shape-preregistration.md:276-290`)。

成果物影響: report が主張できる登録区分が「研究全体の事前登録」から「探索開示済み、formal cohort 前の事前登録」へ狭まる。

提案: 冒頭と machine spec に「格子・幅・非飽和結末の選択は T-2418 後であり、探索に対する事前登録ではない。前向きなのは未実施 formal cohort の測定・判定規則だけ」と置く。`observed_saturation_status` は `exploratory_interpretation_not_formal_verdict` 相当へ改める。

### [real] [nit] 「飽和または域内非飽和」という上位の選言は恒真である

根拠: valid cohort には `saturated-in-all-workloads`、各種 `not-observed`、それ以外には `invalid` を割り当てるため、allowed verdict 全体は全結果を覆う (`plan.md:509-521`)。「飽和位置または域内非飽和を主張する」という上位文だけなら偽になる観測はない。これは完全な報告規則としては正しいが、反証可能な研究仮説ではない。

成果物影響: 数値・受理集合は変わらず、report の headline を「実証主張」から「事前登録済み結果分類」へ変更する。

提案: 上位選言を科学的主張と呼ばず、反証可能な主張を「全 workload で登録述語を満たす飽和位置が存在する」に限定する。非飽和はその反証結果として報告する。

### [refuted] [nit] 個々の停止条件・失敗条件・格子規則は恒真ではない

根拠:

- 停止条件は、1 workloadでも連続2区間のどちらかが `qhat>0` または `U>0.05` なら偽になる (`plan.md:145-151`)。
- 失敗条件は、27 cell、各5 rep、全 certified、anomaly 0、全 hash 相異、欠測なし、CV<2%、時間内なら全て偽になる。逆に1 rep欠測や hash 衝突で真になる (`plan.md:164-178`)。
- 格子規則は 8944 µs の欠落、9999 µs超、または 8944→10944 以外の raw 符号化で偽になる (`plan.md:26-60`)。

成果物影響: なし。問題は規則自体の恒真性ではなく、量子化と consumer 不在で実効性が失われる点にある。

提案: 各規則に上記の正例・反例を非規範的な例として添え、後続 driver のテスト設計に使う。

### [real] [must-fix] correctnessと欠測の machine spec は先例の実 gate より曖昧である

根拠: plan は `required_verdict="certified"` とするが、その field の所在を定めない (`plan.md:436-443`)。実際の T-2418 report point は `certified=false` と `correctness_verified=true` を同時に持つ (`backoff_extended_sweep.py:1088-1107`、上記 report JSON `:1`)。先例 loader は report の真偽値を信じず、admitted WAL の committed attempt、expected genome集合、重複、rep index、有限な正 throughput、abort `[0,1]`、各 verify record の `certified` を検査して導出する (`backoff_extended_sweep.py:1023-1111`)。plan の missingness は件数と抽象的な「範囲外」だけで、field別範囲・label/genome/raw値・attempt・campaignとの結合を機械可読に固定していない (`plan.md:523-547`)。

成果物影響: 実装解釈によって全 cell が誤って invalidになるか、偽造された `correctness_verified=true` を formal sampleとして受理し得る。

提案: verifier record の exact pathと意味を指定し、formal verdictは certified campaign viewとWALから再導出することを要求する。expected workload×point×rep集合、rep index、型・範囲、genome/raw/label対応、attempt束縛も machine spec に列挙する。

### [refuted] [nit] binary相異要求そのものは先例と同じ強さに達している

根拠: T-2418 は全5 genomeについて exact `BuildResult`、trace-disabled、canonical genome束縛、完全SHA-256、全相異、件数完全性を要求する (`backoff_extended_sweep.py:291-321`)。plan はformal cohortの全9 genomeについて同じ要素とamount集合完全一致を要求する (`plan.md:444-462`)。一般 helper `_require_distinct_static_binary_hashes` の「2未満なら成功」という穴 (`backoff_extended_sweep.py:226-255`)には依存しない設計になっている。

成果物影響: binary identity の受理集合を追加で狭める必要はない。

提案: 後続 wave が generic helperだけを呼ばず、登録9 genome完全性を要求する専用経路を実装することを acceptance 条件にする。

### [real] [must-fix] docs-only 文書は現時点では後続走を拘束しない

根拠: 現行 repoで `IZANAGI-B10-STATIC-TAIL-SPEC`、`static-tail-preregistration`、`must_parse_entire_spec` を `git grep` した結果はいずれも0件だった。plan が持つのは future driverへの規範だけである (`plan.md:549-576`, `plan.md:582-591`)。宣言値に consumer が無ければ保証にならない同型は F699 に実例がある (`docs/failures.md:19633-19649`)。

成果物影響: 本 wave終了時点では既存系列の受理集合は1件も変わらず、別格子で走った後続成果物を止められない。その成果物を「本事前登録に準拠」と呼ぶ根拠もない。

提案: 本書の効力を「将来実装の規範と、formal結果前にbytesが存在したことの証拠」に限定する。「拘束している」とは書かず、次 waveでconsumerが実装・発火確認されるまで formal投入不可と明記する。D1813は格子を投入前に凍結する二段構成を認めるため (`d1813.md:3-13`)、本 waveでdriverを書く必要はない。

### [real] [must-fix] 探索値の混入禁止は現 spec だけでは機械判別できない

根拠: spec は禁止 booleanと探索 abscissaを持つ (`plan.md:206-208`, `plan.md:342-346`, `plan.md:545-576`)。しかし formal sample の各 rep に source run kind、campaign lock、attempt/WAL record digestが無い。T-2418成果物には top-level identityはあるが、数値を別の「formal」reportへコピーすれば値だけから出所を判別できない (`backoff_extended_sweep.py:1149-1194`)。D1848はcampaign identity分離を要求する (`d1848.md:15-26`)が、consumerが照合しなければF699型の宣言に留まる。外部成果物を指示でなくデータとして扱う義務は `CLAUDE.md:88-95`。

成果物影響: 2000/4000/9999 µs の探索repがformal CV・`qL`・`U`へ入り、飽和位置と集約 verdictを変更し得る。

提案: formal observationごとに `source_run_kind`、campaign id、campaign-lock digest、attempt id、rep index、WAL record digest、source measurementを必須化する。解析はformal campaignのadmitted WALから再構成し、入力reportの `qL`、`U`、verdict、correctness booleanを権威として受け取らない。

### [real] [裁定パッケージ候補] 正値のpointwise meaning witness不在はformal物理量主張にも残る

根拠: plan自身が `static_meaning_witness_status=unestablished`、新gate不要とする (`plan.md:427-429`)。T-2418一次資料もPython codec/wire構成までしか直接保証せず、この境界が既存系列共通だと明記する (`t2418-explore-README.md:24-37`)。過去には符号化衝突で別条件を測った実在事例がある (`docs/failures.md:19972-19997`)。brief はこれをT-2501として明示的にscope外とする (`brief.md:18-20`)。

成果物影響: reportが「物理 8000 µs」等と表示しても、認証されるのがraw値の異なるbinaryまでに留まる可能性がある。

提案: 本 waveでは実装要求しない。裁定では、formal投入前にT-2501を必須化するか、主張を「登録raw符号化値に対する応答」まで狭めるかを選ぶ。

## 親 brief への攻撃

- 上端1000 µsと表現上限9999 µsは確認できた。現物は `orchestrator/campaign/backoff_extended_sweep.py:55-79`。この2命題は正しい。
- `git grep b10-backoff-static-tail` が0件なのも現HEADで再現した。ただし、これはexact文字列の不在しか証明せず、動的glob consumerや同義の既存材料の不在は証明しない。F717が要求する母集合限定 (`docs/failures.md:19940-19960`)をbriefは書いていない。
- 「docsに静的tailの事前登録は無い」は、「専用のformal格子・停止基準を持つ文書は無い」なら正しい。絶対表現では過大で、D1813が探索3点、二段構成、formal投入前の凍結を既に登録している (`d1813.md:3-13`)。
- 「B-10の過抑制域が本waveの研究前進」は言い過ぎである。D1678は過抑制域の機序を査読要求まで見送った (`docs/decisions.md:51202-51218`)。後発D1813はtail測定を認めるので本wave自体は正当だが、planの主張はabort飽和の記述であり機序ではない (`plan.md:116-153`)。正確には「探索後の静的右tailのformal特性化」である。
- briefの「純増=前向き固定だけ」 (`brief.md:43-46`) は、formal cohortに対してのみ正しい。格子・5%幅・非飽和結末は探索結果を見た後に選んでおり、研究全体に対する前向き固定ではない。
- briefがdocs-onlyをprovisionalとしたことは妥当で、現時点でdriverを追加すべき実在要件は見つからない。必要なのは文書の保証範囲を正直に狭め、次waveの投入前条件としてconsumer実装を固定することである。

## 総括

停止述語の最大の欠陥は、4桁量子化を精密測定として扱い、短い最終区間で偽の飽和を作れる点である。  
さらに正値ゼロ分散では自由度が未定義となり、現規則はvalid cohortへtotalでない。  
前向きなのはT-2418後・formal cohort前に固定する規則だけで、探索結果への事前登録ではない。  
binary完全性は先例相当だが、correctness・欠測・provenanceのmachine契約は先例の実loaderより弱い。  
docs-onlyは正当だが、現時点の文書は規範と時点証拠に留まり、後続走を機械的には拘束しない。  
量子化、入力由来、correctness導出、保証範囲を文書で閉じてから凍結すべきである。