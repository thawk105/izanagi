# 段 3 敵対検査結果

静的検査のみを行った。pytest、評価器、artifact 生成は実走しておらず、緑とは報告しない。

## 所見

### 1. schedule authority の停止理由

- **所見**: production の生値をそのまま使う限り型矛盾は実在するが、「どんな production 実装でも C05 を満たせない」は過大であり、厳密な projection adapter を新たに規定すれば validator を緩めず解消できる。
- **根拠**: `orchestrator/campaign/s8c_schedule.py:75-114,167-249`、`orchestrator/campaign/s8c_generation_projection.py:22-26,173-212`、`orchestrator/campaign/p3_autonomous_workload_trial.py:1650-1652,2585-2607`
- **成果物影響**: 現状のままでは schedule は発行不能で C05 は schema 不在のままになる一方、根拠のない wrapper を発明すると schedule の digest、全 cell の初期状態参照、後続レポートの authority が自己整合した偽値になる。欠陥の所在は production の正式な文字列・空 whiteboard ではなく、schedule 側の authority schema と canonical projection 規則の欠落である。
- **反証可能性**: 現行凍結文書内に `leakproof_context`、空 whiteboard、cell 別 descriptor binding を schedule の非空 JSON 表現へ写す exact 規則が見つかり、その規則から `validate_authority()` を通る値を一意に再生成できれば誤りである。

### 2. campaign_id の停止理由

- **所見**: `campaign_id` を正当に発行する現行経路はなく、site 未確定という停止理由は正しい。
- **根拠**: `docs/phase3-8c-preregistration.md:157-158,190`、`orchestrator/campaign/p3_autonomous_workload_trial.py:1143-1186,1270-1285`、`orchestrator/campaign/p3_s4_loop_trigger_gating.py:423-437`、`orchestrator/campaign/trial_registry.py:4802-4814`
- **成果物影響**: manifest loader は任意の非空 `campaign_id` を受けるが、production は実 site から再計算して exact 一致を要求するため、発明した値は launch 時に拒否されるか、特定 site だけを暗黙に選んだ manifest になる。
- **反証可能性**: admitted site 全てについて同じ 6 campaign ID が得られる実測、または正式 site と environment を一意に定める設計文書の規則が示されれば誤りである。

### 3. freeze_id の停止理由と恒真変異

- **所見**: `freeze_id` の権威規則は不在であり、再導出一致だけでは選択の正しさを検査できない。
- **根拠**: `docs/phase3-8b-descriptor-design.md:538-543`、`orchestrator/campaign/trial_registry.py:1331-1371`、`s2-plan.md:21,104-123`、`docs/failures.md:6841-6856` の F207
- **成果物影響**: 予定 builder への具体的一行変異 `freeze_id = freeze_validation.tip_record_sha256` → `freeze_id = manifest_sha256` は、genesis と binding を同じ式で再生成する限り `--check`、18-field 変異、P/C topology の全てを通る。certified 選択はまだ閉じていても、binding と attempt 台帳が別の freeze identity を正として固定する。
- **反証可能性**: production 導出器と独立に設計文書から `freeze_id` の exact domain と値を抽出する検査があり、この一行変異だけで赤になることを確認できれば誤りである。

### 4. genesis と反復数 n

- **所見**: 「正しい genesis は n なしに発行できない」は正しいが、「binding の発行自体が valid genesis を要求する」は実装上は誤りである。
- **根拠**: `docs/phase3-8b-descriptor-design.md:464-484,518-543`、`docs/phase3-8c-preregistration.md:218-225`、`orchestrator/campaign/trial_registry.py:1427-1439,1442-1485`、`orchestrator/campaign/attempt_registry_core.py:483-509`
- **成果物影響**: P の canonical path に任意 bytes を置き、その SHA-256 を binding に書けば `validate_preregistration_binding()` は genesis を parse せず受理するため、n 非依存で binding artifact は技術的に発行できる。しかし正しい全反復 slot 集合ではなく、後段 reservation は拒否するか、6 個の `r0/a0` だけなら正式設計に反して一部試行だけを受理しうる。
- **反証可能性**: `load_effective_binding_at_commit()` が genesis を `load_attempt_registry()` へ通し、登録済み n、全 replicate、全 attempt、exact retry reason と完全一致させる現行呼び出しが見つかれば誤りである。

### 5. 受理集合の拡大

- **所見**: certified 発効集合は広がらないが、P/C binding validator の受理集合は明確に広がり、formal non-certifying 経路にも必要な前提を与える。
- **根拠**: `orchestrator/campaign/s8c_preregistration_evidence.py:3075,3163-3193,3584-3598`、`orchestrator/campaign/trial_registry.py:3614-3629,3963-4009`
- **成果物影響**: `SATISFIABLE_CONDITION_IDS` が空なので certified 選択・certified report は増えない。一方、従来 binding 不在で拒否された P/C history は受理される。non-certifying launch はさらに trial registry registration を必要とするため、3 artifact だけで直ちに完走可能にはならないが、12 predicate を参照しない経路の前提が新たに成立する。
- **反証可能性**: artifact 追加後も正しい P/C を `validate_preregistration_binding()` が拒否し、また non-certifying admission が12 predicate 全件を再計算することを示せれば誤りである。

### 6. machine_checkable と負の対照の登録状態

- **所見**: 現状は machine-checkable 10 条件と evaluator 10 本が一致し、C03/C08 は static evaluator に限定され、artifact 追加だけで SATISFIED へ移る条件はない。
- **根拠**: `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:149-151,226-228,357-359`、`orchestrator/campaign/s8c_preregistration_evidence.py:3075-3087,3164-3193,3584-3598`、`orchestrator/tests/test_s8c_preregistration_predicates.py:2769-2813,3529-3539`
- **成果物影響**: certified 選択、正式レポート、台帳の certified flag は不変である。C03/C08 は manifest/binding bytes を読まず source shape だけを見るため、artifact 発行を両条件の進捗証拠にしてはならない。
- **反証可能性**: contract の true 集合、`_MACHINE_EVALUATORS`、`SATISFIABLE_CONDITION_IDS` のいずれかが提示行と異なる commit、または C03/C08 が artifact bytes を読む分岐が示されれば誤りである。

### 7. C05 に関する親の実測 1

- **所見**: schedule blob を実際に置けることを前提にすれば、demo authority と実 authority の違いで C05 結果は変わらず、親の `UNSATISFIED / schedule-consumer-unreachable` 予測は正しい。
- **根拠**: `orchestrator/campaign/s8c_preregistration_evidence.py:738-748,2082-2088,2090-2154,2156-2191`
- **成果物影響**: evaluator は schedule を decode せず、1 byte の blobでも存在すれば schema 不在理由を越える。この reason 遷移は schedule の正当性を証明せず、gap ledger が「schema は成立した」と誤読される危険がある。
- **反証可能性**: `_evaluate_c05()` 内に artifact bytes の canonical parse、schema 検査、authority 再導出へ依存する分岐が追加され、実 authority によって status または reason が変われば誤りである。

### 8. snapshot 更新

- **所見**: 12 行を exact に保ったまま C05 の一行だけを置換する更新は検査の緩和ではないが、現時点の direct probe は実 repo snapshot の実測ではなく合成 artifact による予測である。
- **根拠**: `orchestrator/tests/test_s8c_preregistration_predicates.py:251-300,3374-3416`、`s2-plan.md:137-161`
- **成果物影響**: C05 を exact `UNSATISFIED / schedule-consumer-unreachable` へ置換するだけなら受理集合は不変である。行削除、部分集合比較、status の EVIDENCE_UNDEFINED 化、C12 の独立 assert 削除が混ざれば、gap ledger の drift を見逃す。
- **反証可能性**: P commit の actual current-repository 評価結果を保存し、pre/post 12 行の差集合が exact `{"C05"}` であることを示せれば「未実測」という部分は解消する。

### 9. planned authority 変異検査の恒真性

- **所見**: 「導出後の18-field mappingを1 fieldずつ変える」検査は digest 被覆を検査するだけで、設計文書から正しい値を抽出したことを検査しない。
- **根拠**: `s2-plan.md:115-125`、`orchestrator/campaign/s8c_schedule.py:210-249,252-278`、`docs/failures.md:15097-15117` の F554、`docs/failures.md:15414-15428` の F570
- **成果物影響**: 具体的一行変異 `authority["leakproof_context"] = {"text": LEAKPROOF_CONTEXT}` → `authority["leakproof_context"] = {"text": "fabricated"}` は、再生成一致を保ち、導出後 field を変える負例でも schedule bytes が変わるため赤にならない。偽の authority digest が全6 cellへ certified 参照候補として固定される。
- **反証可能性**: 設計・production の歴史 bytesを独立 parserで読み、期待 projection を literal規則から作るテストがこの一行変異を単独理由で殺せれば誤りである。

### 10. C05 negative_control_id の実体

- **所見**: C05 の登録名は initial-state bitflip だが、registry 共通ケースが実際に変異するのは supervisor の consume bypass であり、bitflip の意味検査は別テストに分離されている。
- **根拠**: `orchestrator/tests/test_s8c_preregistration_predicates.py:1104-1126,1200-1211,2816-2848,3456-3496`
- **成果物影響**: 現状は両テストがあるため拒否力は存在するが、ID の登録一致だけを数えると bitflip テストを削除しても境界テストは緑になる。C05 の authority digest 破壊耐性を過大報告しうる。
- **反証可能性**: registry の `negative_control_id` から bitflip test の実在と失敗を直接照合する閉包、または共通ケース自体が bitflip bytesを投入する形へ統合されていれば誤りである。

### 11. freeze 範囲

- **所見**: 停止した現プランは凍結範囲を変更しないが、欠落している canonical authority projection を新設 builder の裁量で定義すると、実質的には C05 証拠の意味を変更する。
- **根拠**: `docs/phase3-8c-preregistration.md:285-301,319-337`、`s2-plan.md:183-190,232-239`
- **成果物影響**: snapshot の実測値更新だけなら version bump は不要である。一方、wrapper の意味、freeze_id、site、slot universe を新規規則として定めるなら、古い condition-freeze record が別意味の証拠を承認したように見えるため `DECIDER_VERSION` bump と次世代 record が必要になる。
- **反証可能性**: 新 builder が既に凍結済みの一意な逐語規則だけを実装し、protected hash、証拠契約の意味、判定入力 projection のいずれも変えないことを field ごとに示せれば誤りである。

### 12. 過去 failure 型の再発

- **所見**: F207/F314/F554 は planned 再導出に再発し、F568 は generator blob identity が全変異を一括で殺して機構固有検出を隠す危険があり、F622 は real artifact check を実装した場合だけ回避できる。
- **根拠**: `docs/failures.md:6841-6856,9373-9397,15097-15117,15379-15395,16460-16472,17481-17496`
- **成果物影響**: 再発を放置すると mutation matrix は KILLED に見えても、値選択・projection・実 artifact 接続の欠陥が生存し、binding、schedule、attempt 台帳が自己整合した誤 authority を参照する。
- **反証可能性**: generator identity failureを除外した機構固有 node が各一行変異で赤になり、着地した3 artifactを開く実 repo testも赤になる mutation probe を示せれば誤りである。

### 13. D992 の未解消な着手順序

- **所見**: 段2が見落とした追加停止条件として、D992 は共有8b ratified freeze が activeになるまで schedule authority 実装へ着手しないと定めており、現 treeには active pointerがない。
- **根拠**: `docs/decisions.md:34821-34841` の D992、`docs/decisions.md:35948-35965` の D1029、`orchestrator/campaign/s8b_ratified_freeze.py:1265-1309`
- **成果物影響**: D1077 が D992 を supersede したと明示せず実装すると、scheduleとその参照を順序違反で発行する。certified値は空のままでも、後続台帳が未批准freeze由来のauthorityを正式artifactとして参照する。
- **反証可能性**: HEADで有効なactive pointer連鎖が存在して`load_ratified_freeze()`が成功する証拠、またはD1077がD992の着手順を明示的に上書きする裁定が示されれば誤りである。

## 再裁定パッケージ案

|択|内容|犠牲になるもの|
|---|---|---|
|A 推奨|D1077の「値ごとの承認」ではなく、導出規則を一括裁定する。official site/env、trial ID規則、master seed、freeze ID、18-field canonical projection、n、attempt数、retry reason exact集合、D992との関係を確定し、必要な decider bump と次世代 freezeを発行する。|ユーザー手番と変更規模は増えるが、3 artifactを正当に発行できる唯一の現行schema経路。|
|B|本waveを停止し、3 artifactもsupport generatorも発行しない。§5と共有ratified freezeの解除を待つ。|T-1380とD1077の完了が延期されるが、受理集合と凍結意味は不変。|
|C|schedule v2、manifest v3、binding v2を設計し、site別identity、n、valid genesis parseをschemaへ持たせる。|既存consumerとの互換性、移行実装、再凍結が必要で最も大きい。|
|D 不採用|demo projection、任意freeze ID、6個の`r0/a0` genesisで形式だけ発行する。|D1077と絶対規律2を失い、binding validatorとformal non-certifying経路の受理集合を不当に広げる。|

## 総括

- **(a) 本 wave を進めてよいか:** 進めてはならない。Aの再裁定かBの延期が必要である。
- **(b) 停止条件:** あり。authority projection、campaign ID、freeze ID、valid genesis、D992の5点が停止条件に当たる。
- **(P1):** 反対。condition-freeze tip digestをseedに選ぶ規則自体が設計文書に無く、決定論的であることは権威性を含意しない。
- **(P2):** 反対。campaign IDはsite未確定で導出不能であり、`h1-on`というtrial ID命名規則も未登録である。
- **(P3):** 賛成。anchor A、内容P、binding-only直子CはD550と現consumerの自己参照回避に一致する。
- **(P4):** 反対。生値は現schemaを通らず、wrapper規則は未裁定である。
- **(P5):** 必要性には賛成、現waveでの正当な発行には反対。任意bytesでbindingを通す実装上の抜け道はあるが、D1077を満たす解決ではない。