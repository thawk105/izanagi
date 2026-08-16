## 総括

- **NO-GO。**
- `"failed"` が直接 certified/admitted へ昇格する経路は反証されたが、failure decision 自体が journal に束縛されない自己申告であり、Layer 3 検査免除を不正に引き出せる。
- admission 成功後に decision を failure shape へ置換する変異が、D217 の欠落検査を通過して report を publish できる。
- 捕捉後の完全性検査や atomic write が失敗すると、元の admission 失敗が report にも journal にも残らない。
- 親 brief の P1 は関門数を過少列挙している。P2 は D431 本文どおり正しい。
- read-only の静的検査のみであり、pytest・実走は行っていない。

## 成立した攻撃

### [1][4] failure decision の自己申告で Layer 3 免除を引き出せる

- 主張: plan の failure shape は key 集合こそ exact だが、`error.type` は任意の非空文字列、`error.message` も自己申告であり、実際に finalizer が失敗した証拠へ束縛されない。plan 自身も journal へ独立束縛しないと明記している (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1175-cell-admission-report/plan.md:35-52,120-121`)。
- 根拠: 現行 producer の最後の防壁は decision の「存在」しか見ない (`orchestrator/campaign/p3_autonomous_workload_trial.py:2172-2177`)。plan は failure decision を completeness の和集合へ加え、同 decision の cell を Layer 3 chain から除外する (`plan.md:15-16`)。通常なら独立 admission、persisted report、fresh rebuild を検査する箇所は `orchestrator/campaign/autonomous_trial_completeness.py:2067-2123` である。
- 成果物への影響: `_finalize_build_cell_admission` が成功した直後に positive decision を valid failure shape へ置換する一変異で、caller は「admission failure」と誤認して critic を止め、欠落検査を通し、Layer 3 を免除できる。既存テストも admission 後の decision 削除変異を明示的な脅威として扱っている (`orchestrator/tests/test_p3_autonomous_workload_trial.py:2580-2609`)。削除は止まるが、置換は plan のままでは生存する。
- 提案する塞ぎ方: failure の受理根拠を cell dict から独立させる。catch だけが生成できる局所 failure record、閉じた `reason_code`、journal の `run-finish` 内 failure projection を一対一照合する。`error.type` は少なくとも `"AutonomousTrialError"` の literal、できれば専用例外型と閉集合 reason にする。`成功 decision → failure decision 置換`、`KeyError と詐称`、failure journal projection の削除・差替えを mutation test に加える。

### [6] 捕捉した admission 失敗が report と journal の双方から消える

- 主張: plan は `AutonomousTrialError` を捕捉して返却経路へ進めるが、failure を journal へ残さない。この後の別例外が元例外を上書きする。
- 根拠: `run-finish` の後にも completeness、Layer 3 chain、journal 再読、atomic write が残る (`orchestrator/campaign/p3_autonomous_workload_trial.py:2242-2275`)。atomic writer 自体も stale tmp や I/O で失敗できる (`orchestrator/campaign/p3_autonomous_workload_trial.py:1283-1293`)。現行 journal の閉集合には admission failure event がない (`orchestrator/campaign/autonomous_trial_completeness.py:39-49`)。
- 成果物への影響: admission failure を decision に変換した後、例えば completeness が赤になるか report tmp が既存なら、report は不在、journal にあるのは理由を持たない `run-finish` だけとなる。正常側 `:2106` では元の admission 失敗を示す durable record が完全に消える。
- 提案する塞ぎ方: `run-finish` に exact admission-failure projection を持たせ、report decision と照合する。専用 event を使うなら、`supervisor-error` が `run-finish` の直前である現行順序 (`autonomous_trial_completeness.py:1209-1210`) を壊さないよう、順序契約も同じ変更単位で改訂する。後続失敗時は元例外を exception chain に保持する。

### [1][6] generation accounting の緩和範囲が producer の実在状態より広い

- 主張: plan は failure decision があれば、最終 role prefix が planner/coder/auditor で終わり、accounting が `pending-pre-invoke-failure` の形を受理する (`plan.md:20-21`)。この組合せの大半は producer が生成しない。
- 根拠: accounting は生成時だけ pending である (`p3_autonomous_workload_trial.py:1129-1145`) が、planner invoke 後に直ちに `partial-generation` へ変わる (`p3_autonomous_workload_trial.py:2506`)。planner/coder/auditor invalid もその状態のまま停止する (`p3_autonomous_workload_trial.py:2508-2514,2558-2564,2614-2620`)。未実行 critic を持つのは harness 後に pending を積んだ形だけである (`p3_autonomous_workload_trial.py:2667-2679`)。再確定は一度限りで、二重確定を拒否する (`p3_autonomous_workload_trial.py:1152-1155`)。
- 成果物への影響: verifier が producer 不可能な planner/coder prefix と pending accounting を受理する。また observed run a の coder-invalid は既存の `partial-generation` 経路なので、誤って pending を必須にすると目的の report 自体が再び拒否される。
- 提案する塞ぎ方: 新規緩和は「planner/coder/auditor が全て valid、harness が存在して検証済み、critic だけ未実行、catch 由来 failure record と一致」に限定する。role-invalid の planner/coder/auditor 経路は既存規則のままにする。

## 反証された懸念

### [1] failure decision の certified/admitted 昇格

反証された。Layer 3 schema は admission status を `"admitted"` または `"historical-not-reclassified"` に閉じ (`orchestrator/campaign/layer3_schema.json:22-35`)、certifying 入力は `"admitted"` 完全一致を要求する (`orchestrator/campaign/layer3_report.py:236-242,584-603`)。completeness も exact key 集合と独立 decision との canonical equalityを要求し (`orchestrator/campaign/autonomous_trial_completeness.py:1941-1965`)、certifying 時は `"admitted"` 以外を拒否する (`orchestrator/campaign/autonomous_trial_completeness.py:1969-1993`)。

`artifact_admission.py` の `decision.admitted` が `!= "legacy-unclassified"` なのは事実 (`orchestrator/campaign/artifact_admission.py:202-204`) だが、cell の failure dict はこの dataclass へ流入しない。decision は campaign bytes から閉じた status で生成される (`orchestrator/campaign/artifact_admission.py:899-912,950-967,1030-1043`)。

`s8c_preregistration_evidence.py` は call 名と literal を見るだけで、成功側でも `EVIDENCE_UNDEFINED` を返す (`orchestrator/campaign/s8c_preregistration_evidence.py:459-475`)。真扱いは exact `SATISFIED` だけである (`s8c_preregistration_evidence.py:275-277`)。

### [2] 混成 trial の免除が admitted cell へ波及する

plan どおり cell 単位に実装されれば反証される。chain は cell ごとの loop であり (`autonomous_trial_completeness.py:2021-2023`)、admitted peer は persisted report から fresh rebuild まで通る (`autonomous_trial_completeness.py:2067-2123`)。plan の `[admitted, failed]` と missing admitted report のテスト (`plan.md:64,82-83`) は trial 単位 early return を殺せる。

ただし failure branch は exact discriminator の検証後にだけ `continue` し、admitted cell 集合を抽出する述語も `admission_status == "admitted"` の完全一致にする必要がある。

### [3] `stop_reason` 詐称による免除

反証された。plan の免除源は exact failure decision であり、`stop_reason` ではない。cell/result への全代入箇所は次の 11 箇所である。

- 初期値 `fixed-generation-budget`: `p3_autonomous_workload_trial.py:2373-2382`
- wall budget: 同 `:2403-2405`
- planner/coder/auditor invalid: 同 `:2508-2513,2558-2563,2614-2619`
- harness terminal: 同 `:2681-2682`。入力は閉集合検査済み (`:1238-1244`)
- critic invalid: 同 `:1884-1887`
- outer supervisor recovery の既存 cell と fallback cell: 同 `:2052-2070`
- handler 内 pending critic failure: 同 `:2087-2103`
- 正常側 pending critic failure: 同 `:2119-2135`

failure 時は critic を呼ばない計画なので、critic の `role-invalid` 上書きも admission exemption の発火源にならない。

### [4] D217 の却下済み cleanup 復活と `:2174` の恒真化

字義どおりの懸念は反証された。plan は finalizer の例外発生地点で一度だけ decision を置き、後処理による欠落推測・再 finalization を明示的に禁止する (`plan.md:13-14,25-31`)。D217 の却下項とも一致する (`docs/decisions.md:10249-10276`)。

また `:2174` は恒真ではない。critic 後に decision を削除する既存変異が実際にこの検査へ到達する (`orchestrator/tests/test_p3_autonomous_workload_trial.py:2580-2609`)。ただし、前述の「欠落ではなく valid failure へ置換する」攻撃は成立するため、存在検査だけでは新しい union に不十分である。

### [5] failure cell を含む `status="complete"`

plan 上は反証された。現行 producer と verifier は stop reason だけで complete を再計算する (`p3_autonomous_workload_trial.py:2161-2170`、`autonomous_trial_completeness.py:1608-1624`) が、plan は双方へ「build cell 全件が positive admitted」を加え、`complete` 変異も拒否テストへ含めている (`plan.md:23,80-81`)。実装では同じ exact positive predicate を共有すべきである。

### [6] 広すぎる `except Exception`

catch の型と字句範囲については反証された。plan は `_finalize_build_cell_admission` 呼出し由来の `AutonomousTrialError` だけを捕捉し、`KeyError` 等は伝播させる (`plan.md:13,120`)。現行 helper 内の同例外は campaign root、reports、既存 Layer 3、Layer 3 validation、mutability の検査に限定される (`p3_autonomous_workload_trial.py:1725-1753`)。成立した問題は catch の広さではなく、捕捉後の durable provenance 欠落である。

### [7] P2 と D431

P2 は反証されず、親が正しい。D431 は最初の production 起動前の gate に限定し、post-run consumer を明示的に除外する (`docs/decisions.md:17878-17885`)。本 finalizer は `_run_workload` の復帰または例外後に呼ばれる (`p3_autonomous_workload_trial.py:2038-2073,2105-2110`)。したがって D431 positive control 義務は発火しない。

### [8] 実走 a/b の呼出し点帰属

観測された二走に限れば親の帰属は支持される。走 a は `do_build=true` (`.../live-abc-g1-20260816a/attempts.jsonl:2`)、coder-invalid (`同:4`)、accounting 後に supervisor-error がない (`同:5`)。coder-invalid は正常 return する (`p3_autonomous_workload_trial.py:2558-2564,2684-2691`) ため `:2106` 側へ進む。

走 b は `do_build=true` (`.../live-abc-g1-20260816b/attempts.jsonl:2`) で、P/C/A 後に `KeyError` の supervisor-error がある (`同:3-7`)。これは `_run_workload` の例外を捕捉する外側 handler (`p3_autonomous_workload_trial.py:2039-2051`) と `:2073` に整合する。

## 親 brief の誤り

- **P1 は誤りというより過少列挙である。** brief は四関門だけを列挙する (`brief.md:70-76`) が、走 a のように requested 3 cell に対して 1 cell で止まり terminal event がない場合、workload coverage も拒否する (`autonomous_trial_completeness.py:1537-1551,1581-1582`)。pending critic が残れば completeness より前にも停止する (`p3_autonomous_workload_trial.py:2172-2173`)。plan は両方を追加変更面へ入れている (`plan.md:20-23`) ため、brief の「4 層」は訂正が必要。
- **P2 は正しい。** D431 の post-run 除外に一致し、positive control は不要。
- **P3 は正しい。** completeness の受理集合を変えるため、新 D と境界テストの同一変更単位が必要 (`docs/decisions.md:4271-4279`)。
- **P4 は静的資料との矛盾なし。** 本 worker は実走していないため、bounded local や dispatch の成功までは確認していない。
- **番号外の実測一般化に誤りがある。** `campaign_root` は `_assert_fresh_campaign_state` より後で初めて cell へ設定される (`p3_autonomous_workload_trial.py:2348-2382`)。同検査は result 構築前に送出可能 (`p3_autonomous_workload_trial.py:401-411`) で、その場合 fallback cell は campaign root を持たない (`p3_autonomous_workload_trial.py:2065-2071`)。また `do_build=False` では root 文字列があっても build finalizer 自体を通らない (`p3_autonomous_workload_trial.py:1769-1774,2360-2365`)。したがって brief `:25-27` の断定は observed role-invalid run a には正しいが、一般には反証される。

## scope 外だが real な所見

- `trial_registry.assert_trial_registry_acceptance` は completeness を通した後 (`orchestrator/campaign/trial_registry.py:2037-2042`)、status を単なる文字列として受け入れ `AcceptedTrial` にする (`trial_registry.py:2602-2605`)。receipt reader も status を非空文字列としか検査しない (`orchestrator/campaign/s8c_acceptance_receipt.py:296-310`)。したがって新しい failure partial report は formal acceptance receipt に入る。現行 receipt は構造的に `certifying=false` (`trial_registry.py:2664-2687`) で、certifying Layer 3 は `true` を要求するため昇格はしない (`layer3_report.py:548-555`)。それでも「partial を formal acceptance receipt に載せるか」は未裁定の consumer 変更なので、段 4 の裁定パッケージへ返すべきである。
- failure-only の build report は、独立 verifier で `campaign_output_root` を省略すると引き続き拒否される (`autonomous_trial_completeness.py:2140-2155`)。runtime report 発行と、単独検証可能な診断成果物の契約が一致しない点は別 scope の実需判断が必要である。