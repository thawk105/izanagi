## blocker

**B1. 物理 executor の出力が ledger と formal consumer へ届く経路がない**

実測アンカー: `s1-brief.md:8-10`、`p3_autonomous_workload_trial.py:429-438,1632-1679`、`reflux_origin_client.py:134-170`、`s2-plan.md:156-166,305-338`。

plan は `result_record_bytes` を実行前の caller 入力として残したまま executor を追加する。一方、現行 origin 経路は sealed batch を読むだけで、`reserve_batch()` / `commit_event()` を一度も呼ばない。scope 外の ledger producer FSM と physical evidence producer がなければ、新しく実行した 33 run を ledger member、result-evidence、formal receiptへ結べない。

成果物影響: formal receipt は欠落するか事前 fixture の別実行を指し、`campaign_runs` と試行台帳の ledger member が別物になる。

**B2. `CampaignSummary.campaign_id` を actual として検査できない**

実測アンカー: `p3_s4_loop_trigger_gating.py:633-640,782-787,811-838`、`s2-plan.md:293-300,323-327`。

`_run_one_iteration_resolved()` は `CampaignSummary` を外へ返さず、戻り値の `campaign_id` を `_with_campaign_location()` が `ident.campaign_id(campaign_cfg)` から再生成する。plan の「`CampaignSummary.campaign_id` 由来」は現行関数を呼ぶだけでは成立しない。また auditor reject は `run_campaign()` より前に戻るため summary 自体がない。

修正には、summary の actual ID、actual layout、物理 attempt の有無、WAL 区間、execution receipt を含む sealed な結果型を物理 harness 内で作り、pre-run reject を evidence 発行可能な reject と区別する必要がある。

成果物影響: plan 値を actual として複写する変異が通り、材料レポートと試行台帳が実際とは異なる campaign root を参照する。

**B3. origin cell は report 作成前の通常 Layer 3 finalizer で失敗する**

実測アンカー: `p3_autonomous_workload_trial.py:2827-2859,3346-3562,3570-3571`、`s2-plan.md:669-714,730-747`。

build cell は常に単数 `campaign_root` を要求して `layer3_report.render()` を実行し、status も通常 admission が positive の場合だけ `complete` になる。plan は downstream completeness と registry を分岐するが、この producer-side finalizer、`admission_decision` の origin 用 closed shape、formal receipt 後の status 決定を変更していない。

成果物影響: exact 33 件の `campaign_runs` を作れても report は admission failure または `partial` となり、lifecycle と試行台帳も complete にならない。

**B4. R1 の lifecycle key 追加が originless の受理集合を広げる**

実測アンカー: `trial_registry.py:204-220,4420-4427,5288-5369`、`s2-plan.md:193-244`。

plan は start key を base と base+digest の二択へ変え、`record_trial_start_once()` の引数間だけで origin binding と digest の同値性を検査する。しかし loader と acceptance は report の `launch_admission.origin_binding` と start row の key 有無を照合しない。そのままでは originless start に `origin_run_plan_sha256` を足した行も loader が受理し、逆に既存形式の origin start も acceptance が通り得る。

`_receipt_lifecycle_snapshot()` で origin binding と key 有無を iff にし、origin 時は固定 path の envelope digest と一致させる必要がある。

成果物影響: originless の受理集合が増え、origin では R1 の参照を欠いた lifecycle が acceptance receipt に収載され得る。

**B5. 提案された completion API は「issued capability + formal receipt」を証明できない**

実測アンカー: `s2-plan.md:694-714`、`reflux_formal_consumer.py:143-175,405-416`、`trial_registry.py:5401-5423,5913-5933`。

`assert_origin_trial_completion(report, run_root, attempt_capability_sha256)` には exact capability も `FormalConsumerReceipt` も渡らない。report が持つのは digest 文字列だけで、`OriginTerminalProjection` 自体にも issuer seal はない。現 acceptance は projection の形と report/lifecycle 間の一致しか検査しない。

producer 時点の exact object から completion token を発行して durable projectionへ束縛するか、receipt bytesを create-only で保存して acceptance が再解決する契約が必要である。

成果物影響:存在しない formal receipt の digest を持つ reportでも33 lock/WAL検査だけで complete となり、acceptance receipt の受理集合がR2より広くなる。

## must-fix

**M1. observation 前の正確な順序と例外分類が未定義**

実測アンカー: `p3_autonomous_workload_trial.py:4645-4705,4751-4768,4833-4858,4966-5056`、`s2-plan.md:116-127`。

plan の順序表から attempt classification が落ちている。固定すべき順序は少なくとも「slot予約 → classification → initial ledger snapshot → identity/envelope → lifecycle start → observation」である。envelope失敗は lifecycle 前なので `OriginPreflightFailure`、lifecycle後のexecutor失敗は report付き `OriginPartialTrialReport` とする境界もtestで固定する必要がある。

成果物影響: classification、observation、lifecycle の順が分裂し、同じ失敗が試行台帳では observed、公開結果では preflight または reportなしpartialになる。

**M2. result-evidence v2 の carrier を裁定待ちのままにできない**

実測アンカー: `reflux_result_evidence.py:62,112-115,167-174,673-704`、`s2-plan.md:469-503,982-988`。

`campaign_lock_ref` は現wireに実在しない。要件14を実装するなら、origin consumer用 `result-evidence/v2` のexact 3 refと、`ResolvedResultEvidence.campaign_lock_ref/campaign_lock` を実装境界として確定する必要がある。これはR1〜R4の再択一ではなく、R4を実装可能にするcarrier決定である。

成果物影響: carrier未確定のままでは lock から物理identityを再導出できず、別layoutのWALを材料レポートへ混入できる。

**M3. 単位所有はfile単位では排他だが、公開signature表が不足している**

実測アンカー: `s1-brief.md:52-60`、`s2-plan.md:810-871`、`p3_autonomous_workload_trial.py:41-65`。

同一production fileを二単位が所有する箇所はなく、file所有自体は排他である。ただし境界表には次が欠ける。

- A → B/C: result-evidence v2 constructor、provenance writer、resolver結果型。
- B → C: executorが生成したrecord bytes、physical root、WAL snapshotの受渡し。
- C → A: completion結果だけでなく、acceptance receiptへ入るorigin cross-binding digest。
- A → C → B → A の順序上、最初から三単位完全並列にはできない。

成果物影響: 統合時に同じ33 runのdigest列を各単位が別々に再構成し、formal receipt、cross-binding receipt、試行台帳の参照が不一致になる。

**M4. plan が見落とした既存 test 更新点がある**

実測アンカー:

- `test_p3_autonomous_workload_trial.py:10624-10693` — `OriginProducerInputs(run_plan=..., result_record_bytes=...)` の共有fixture。
- `test_reflux_formal_consumer.py:194-218` — `evaluate_formal_origin()` 全呼出しの共通kwargs。
- `test_p3_autonomous_workload_trial.py:3876-3975` — `_finish_trial` のfinalizer回数とstatus順序をASTで固定。
- `test_reflux_originless_compatibility.py:126-143` — origin-enabled比較bundleの構築点。

前二件は署名変更で確実に赤になるが、plan の影響一覧は後段test本体だけを挙げている。三件目はB3を正しく直す際の制御構造変更で赤になり得る。

成果物影響: repo受入が赤のままになるか、既存のstatus/finalizer保証を削って緑化すると通常reportの値と受理集合が変わる。

**M5. lifecycle start の現行key数は14ではなく15**

実測アンカー: `trial_registry.py:204-210`、`s2-plan.md:195-201`。

plan の「現行14 key」は誤りで、実在する集合は15 keyである。提示コードをそのまま実装するとbase集合から既存fieldを落とす危険がある。

成果物影響: lifecycle start rowのbytesが変わるか、既存行がschema違反となり、全trialのacceptanceが停止する。

## nit

**N1. claimed-current なproduction名の不実在は0件**

`PreparedCampaignIdentity`、`_assert_reservation_preflight`、`ReservationCheck.ensure_remaining`、`_run_one_iteration_resolved`、`decode_campaign_lock_bytes`、`_wal_trigger`、`_validate_bijection`、`build_report`、各completeness/acceptance関数は指定位置に実在した。`OriginCampaignRun` 等は明示された新設名なので不実在誤記には数えない。`campaign_lock_ref`だけはM2のとおり現wireに存在しない。

成果物影響: 名前解決そのものによる破損はないが、M2とM5のschema不一致は残る。

## 意味のある分割

9〜18を現scopeの1 waveで完了する量ではない。planの二分案も、第二waveにledger producerが無いため完結しない。意味のある切断は次の三段である。

1. contract wave: R1、要件9〜11、execution-provenance v2、result-evidence v2、要件13〜17、fixture public正例、originless不変。名乗りは「8c physical binding contract」、結線完了とはしない。
2. producer wave: sealed executor、actual summary結果型、physical evidence writer、ledger producer FSM、witness normalizer、残時間とauditor入力。失敗時はfail-closedで、まだregistry completeとはしない。
3. publication wave: origin report、producer status、completeness、cross-binding、Layer 3 inspection、registry acceptance、材料レポートrenderer。ここで初めて要件18とR2を完了扱いにする。

第一段だけなら既存の0/3と本番authority 0件を保ったままlandでき、次waveが使うexact wireを固定する中間状態になる。

## 裁定パッケージ候補

- `s1-brief.md:8-10` でscope外としたledger producer FSM、witness normalizer、材料レポートrendererは、要件12・18とR2の公開正例に実際に必要である。scopeを広げないなら本waveの完了名をcontract waveへ狭める必要がある。
- `docs/phase3-8c-wiring-design.md:645-647,903-904` に反して、planは材料レポートrendererを触らない。`layer3_report.py` の読取りhelperだけでは、ledger/result-evidence/33runとD1674の保証限界が材料レポートへ出ない。
- `autonomous_trial_completeness.py:2105-2108`、`trial_registry.py:693-697`、`reflux_origin_binding.py:600-603,649-650` はfixture scopeを固定している。現状0/3では問題ないが、本番authority発行後もproduction originを拒否するため、production解禁waveの実在課題として別パッケージ化すべきである。

## 総括

判定: **作り直し**。静的検査のみで、testは実行していない。

最大の3点:

1. executorの新しい物理結果をledger/result-evidence/formal consumerへ渡すproducer経路がない。
2. origin reportは通常Layer 3 finalizerとstatus計算でcompleteになる前に止まる。
3. R1 lifecycleとR2 completionのdurableな受理契約が不足し、originless受理集合も広がる。