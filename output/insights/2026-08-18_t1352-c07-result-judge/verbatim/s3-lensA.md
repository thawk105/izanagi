```text
静的レビュー。必読 path は全て読了し、実装変更と pytest 実行はしていない。

A1
[severity: must-fix] [攻撃シナリオ] 親 brief の「4件赤」を C07 の有効化結果として採用すると、壊れた変異の構造赤を判定異常と誤帰属する。実際の変異は key 7 に `_evaluate_c01` を登録し、負例 dict だけに C07 を追加している。C07 の負例分岐はなく、test は `_negative_control_case` の AssertionError で止まる。
[根拠 /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/s1-brief.md:29-39; /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/probe_mutate.py:5-11; orchestrator/tests/test_s8c_preregistration_predicates.py:653-743,1974-2027]
[提案] 実在する `_evaluate_c07`、実際の evaluator 経路、負例分岐、同一 contract を一度に揃えた最小変異を `evaluate_all` まで通し、前後で C07 の理由だけが変わることを測る。現行の4件赤は C07 判定の証拠から除外する。
成果物影響: 4件赤は「C07 が UNSATISFIED」ではなく構造変異赤として台帳へ記録し、certified 選択・受理集合・公式レポートは変更しない。

A2
[severity: must-fix] [攻撃シナリオ] 新設予定の `_evaluate_c07` が直接テストでは動いても、production の `PredicateRegistry.evaluate_all` からは呼ばれず、C07 は従来の `FLOOR_JUDGE_CONSUMER_UNDEFINED` のままになる。
[根拠 /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/artifacts/s2-plan.md:142-193,211-217; orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:294-301; orchestrator/campaign/s8c_preregistration_evidence.py:1815-1848,1902-1934]
[提案] C07 を実効 gate にするなら contract の `machine_checkable`、registry、reachability、generation/freeze を同一束で更新し、変異を `evaluate_all` で検証する。更新を次 wave に残すなら、本 wave の成果物を静的 lint と明記し、gate の実効化とは報告しない。
成果物影響: 現状の C07 status と受理集合は不変。実効化を主張する場合だけ、condition-freeze、reason code、certified 選択の参照を新世代へ更新する。

A3
[severity: should-fix] [攻撃シナリオ] `accept_trial` が stale であることを C07 全体の受理経路が反転不能だという根拠に一般化すると、実在する `assert_trial_registry_acceptance` と CLI 経路を見落とし、正しい配線の裁定を先送りする。
[根拠 orchestrator/tests/test_s8c_preregistration_invariant.py:427-449; orchestrator/campaign/trial_registry.py:2557-2568,2993-2999; orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:281-297]
[提案] 「現行 C07 contract の入口名が不存在」と「将来の正しい acceptance consumer を追加不能」を分離する。C07 を更新する場合は実在する acceptance 入口、result judge、receipt、generation hash を一束として再測定する。
成果物影響: P1 は実測事実ではなく provisional な scope 判断へ格下げし、実在入口への binding がない間は certified 選択を受理しない。

A4
[severity: must-fix] [攻撃シナリオ] caller が任意の floor bytes と一致する hash、`env_tag`、`measurement_head` を用意すれば `verify_floor_bytes` を通せる。さらに、検証結果を global state に残す、例外を caller が status へ変換する、失敗後も publish を呼ぶ経路が残る。
[根拠 /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/artifacts/s2-plan.md:36-55,241-245; orchestrator/campaign/s8b_ratified_freeze.py:1355-1373; orchestrator/campaign/s8b_holdout_admission.py:2072-2109; docs/phase3-8c-preregistration.md:231-239]
[提案] floor ref は caller の自己申告値ではなく `load_ratified_freeze()` の `floor_source` と ledger から導出した sealed object だけを受理する。judge は純粋関数にし、検証成功、変更 bytes、検証例外、共有 state の有無で数値結果が変わらないことを試験する。floor 検証失敗時は publish と receipt を中止する。
成果物影響: floor 不一致・例外は official_status の別値へ変換せず、3表と certified 選択を生成しない。台帳は ratified source の path/hash を参照する。

A5
[severity: must-fix] [攻撃シナリオ] 実測値を見た後に、型と範囲だけ正しい `delta_min`、`sd_max` を caller が渡して status を反転させる。
[根拠 /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/artifacts/s2-plan.md:70-84; docs/phase3-8b-descriptor-design.md:464-484; docs/phase3-8c-preregistration.md:231-239]
[提案] judge は raw params ではなく、値、unit、direction、n、prereg commit、canonical hash を持つ事前登録済み sealed params のみ受理する。契約値が不正なら個別 C3 を `INDETERMINATE` にするのではなく、事前登録そのものを未発効にして正式結果へ数えない。
成果物影響: params hash または prereg binding 不一致時は official_status を出さず、certified 選択集合と正式試行台帳から当該 run を除外する。

A6
[severity: must-fix] [攻撃シナリオ] raw prediction record、caller が事前計算した median/delta、correctness gate 未通過の observation を judge に渡し、C1 と C3 を成立させる。
[根拠 /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/artifacts/s2-plan.md:44-55,90-112; docs/phase3-8b-descriptor-design.md:441-456; orchestrator/campaign/s8b_verdict.py:348-375,841-856,1185-1198]
[提案] raw dict と caller 計算済み delta を拒否し、検証済み prediction、correctness gate 済みの trace-disabled observation、manifest/descriptor/measurement commit に束縛された sealed input から judge 内で median と対差を再導出する。
成果物影響: 未検証入力、gate 不通過、source hash 不一致は C1/C3 を成立させず、official_status は生成せず、受理集合へ追加しない。

A7
[severity: must-fix] [攻撃シナリオ] `conditions` を3要素に見せつつ同じ条件を重複させる、または H1 の delta が H2 の失敗を平均で隠す。計画は「必要な holdout domain」と一つの delta vector を許しており、3要素の長さだけでは実質2条件を防げない。
[根拠 /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/artifacts/s2-plan.md:19-30,90-99,105-112,167-173; docs/phase3-8b-descriptor-design.md:441-451; orchestrator/campaign/s8b_verdict.py:883-903]
[提案] condition ID を `{on_off_prediction_difference, swapped_follow_through, paired_repeat_contrast}` の重複なし完全集合として検証し、H1/H2 の expected domain を sealed prereg から独立に導出する。C3 は holdout ごとに評価し、`INDETERMINATE` の優先順位を含む3値の真理値表を固定する。
成果物影響: 条件 ID の欠落・重複、holdout 欠落、片側だけの成立は certified 選択を成立させず、該当 cell を受理集合へ入れない。

A8
[severity: must-fix] [攻撃シナリオ] 生成行から predeclared cell 集合を作り、それを同じ生成行と比較するため、manifest と observations を同時に削っても set equality が成立する。6個なら任意の cell ID でも通る。
[根拠 /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/artifacts/s2-plan.md:126-131; orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:278-297; orchestrator/campaign/trial_registry.py:500-512; docs/phase3-8c-preregistration.md:213-217]
[提案] expected set は生成物から導出せず、ratified manifest と append-only registry から独立に取得する。`H1/H2 x on/off/swapped`、unique trial/campaign ID、canonical order、manifest hash、registry hash を全て検証してから生成行と完全比較する。
成果物影響: 6 cell 以外、任意 ID、manifest と registry の同時改変は3表を生成せず、certified 選択集合と台帳の cell 集合を空のままにする。

A9
[severity: must-fix] [攻撃シナリオ] 新しい `official_status` 表を出力しても、現行 acceptance は report の任意の非空 `status` 文字列だけを受理し、result judge や公式表を参照しない。順位表や自由文字列が certified 経路へ混入する。
[根拠 /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/artifacts/s2-plan.md:133-138,247-257,259-269; docs/phase3-8c-preregistration.md:500-504; orchestrator/campaign/trial_registry.py:2832-2843,2993-2999; orchestrator/campaign/s8c_acceptance_receipt.py:335-343,368-376]
[提案] acceptance consumer が result judge の3表、hash、6 cell 集合、三値 enum、params hash を検証し、certified selector は `official_status` のみを消費するよう配線する。現行 receipt は構造的に `certifying: false` なので、この配線がない限り正式受理を宣言しない。
成果物影響: `official_status` の欠落・未知値・表 hash 不一致は receipt を非発行とし、順位や report の `status` だけでは certified 選択・受理集合を増やさない。

A10
[severity: must-fix] [攻撃シナリオ] caller が repo 内 path、symlink、既存成果物を指定する、または3表の1つを書いた後に次の書込みが失敗し、部分表が後段 consumer に拾われる。
[根拠 /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/artifacts/s2-plan.md:114-130,247-257; /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/ruling-full8.md:77-84; orchestrator/campaign/pegasus_floor_scoping.py:4-5]
[提案] 正式 run の出力先を repository 外の検証済み create-only target に限定し、symlink と既存 bytes を拒否する。3表を staging へ全て生成・hash 検証してから atomic に公開し、途中失敗時は表も receipt も残さない。
成果物影響: path、hash、atomic 公開のいずれかが不成立なら3表を受理集合へ登録せず、台帳には未公開として記録する。

A11
[severity: must-fix] [攻撃シナリオ] 静的 evaluator が validator の呼出し、3表 marker、condition 集合を見つけても、返値を捨てる、`if False` 側だけで呼ぶ、status を固定値で返す実装を通す。
[根拠 /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/artifacts/s2-plan.md:155-179,201-217; orchestrator/campaign/s8c_preregistration_evidence.py:291-322,598-640; orchestrator/tests/test_s8c_preregistration_predicates.py:1260-1392]
[提案] 「呼出しが存在する」だけでなく、validator の返値が status、conclusion、3表の出力へ到達する data flow を検査する。ignored return、dead branch、固定 SAT、条件重複、cell validator の結果未使用を各々1変異として、production evaluator の同一入力で理由が一つだけ変わることを確認する。
成果物影響: data flow が証明できない consumer は `EVIDENCE_UNDEFINED` のままとし、C07 を UNSATISFIED や certified として台帳へ記録しない。

A12
[severity: must-fix] [攻撃シナリオ] judge と静的関数だけ land しても、実走側は H1/H2 の正式 workload、schedule、attempt registry、correctness gate、formal acceptance、receipt、certified selector を使わないため、成果物が実際の受理を変えない。
[根拠 /work/1/SFC/tanab/dev-wave-jobs/2026-08-18_t1352-c07-result-judge/artifacts/s2-plan.md:259-271; docs/phase3-8c-preregistration.md:199-239,482-511; orchestrator/campaign/p3_autonomous_workload_trial.py:191-195,641-705; orchestrator/campaign/trial_registry.py:2557-2568; orchestrator/campaign/s8c_acceptance_receipt.py:23-32]
[提案] 次を scope 外の裁定パッケージ候補として分離する。(1) condition 7 contract、reachability、condition-freeze、DECIDER_VERSION の更新、(2) H1/H2・1m/48・off/swapped・schedule/master seed・attempt registry の実走層、(3) correctness/prediction/observation の sealed input 層、(4) trial registry と公式3表の acceptance 配線、(5) receipt、ledger、certified selector、外部 atomic publication、(6) `evaluate_all` を通る mutation matrix。現 wave の scope は新 judge、静的 evaluator、直接テストだけであり、これらを実装済みとは扱わない。
成果物影響: 上記 package が閉じるまで C07 は EVIDENCE_UNDEFINED、正式 run は未発効、certified 選択と受理集合は増加なしとする。
```

## 総括

親 brief の4件赤は C07 の実効変異を測っておらず、P1 の一般化は成立しない。  
新 `_evaluate_c07` も現行 `evaluate_all` からは到達不能で、直接テストだけでは gate にならない。  
最重要の設計穴は caller 自己申告の floor refs、params、manifest、prediction を信頼できる点である。  
C3 は per-holdout の完全 block、sealed input、事前登録 params まで束縛しないと緩む。  
現行 acceptance と receipt は official_status を消費せず、certifying も false のままである。  
CV、SD 合算、unpaired 退避を主量にしない点と既存テスト緩和禁止は静的には守られている。  
実装後も、scope 外の実走・受理・receipt・certified selector 層を別裁定 package として閉じる必要がある。