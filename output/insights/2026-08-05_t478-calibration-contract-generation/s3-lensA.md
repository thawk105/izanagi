判定は **NO-GO**。世代分離の方向性以前に、提案された順序では g2 閉包を生成できず、切替後の閉鎖も機械的に保証されていません。

### 1. `pending` g2 から g2 成果物を生成できない

[severity: must-fix]

- 攻撃シナリオ: 段2では g2 を `pending` にしたまま g2 floor protocol を生成するが、builder は `lookup(env_tag)`、すなわち g1 current から contract hash を取得する。そのままなら g1 protocolになり、g2を強制すれば validator が拒否する。段3の selector seal も同じ builder で再導出するため g2 committed protocol と一致せず、silo producer も current g1を取得する。手順どおりでは g2 closure が完成しない。
- 根拠: `s2-plan.md:148-155,198-205,278-283`、`orchestrator/campaign/s8b_floor_campaign.py:365-440`、`orchestrator/campaign/s8b_prediction_runner.py:1457-1473,1538-1570`、`orchestrator/campaign/silo_ladder_rung1.py:1928-1968,4417-4440`
- 提案: `pending` を一般の `lookup()` に露出させず、protocol/selector 構築専用の型付き staging resolver を設計する。測定を伴う silo evidence は `current_unverified` への遷移後に作り、後述の activation receipt ができるまで certified 選択を閉じる。この順序が U-8 の2 commit制約と両立しないなら、その衝突自体を裁定事項へ戻す。
- **成果物影響**: g2 selector proof と silo evidence が作れず、certified 選択の受理集合は空、材料レポートは g2 floor/oracle 参照欠落、試行台帳は g1のままか禁止された pending 測定を記録する。

### 2. 「閉鎖」「再開時 bundle hash」が実在する gate 入力になっていない

[severity: must-fix]

- 攻撃シナリオ: 段3 commitで current が g2になった直後、段4の検査完了前に停止・障害・別プロセス起動が起きる。既存 entrypoint は bundle hash や migration state を受け取らず current lookup だけで進むため、未検証 g2で campaign を開始できる。段0の「停止」は稼働中 job の drain/epoch fence も定義していない。
- 根拠: `s2-plan.md:276-281` は pointer反転後に検査し、再開時 sentinel を記述する一方、実入力を定義していない。floor入口は `orchestrator/campaign/s8b_floor_campaign.py:2670-2709`、oracle gate は `orchestrator/campaign/s8b_oracle_driver.py:737-803`、P3は `orchestrator/campaign/p3_s4_loop_trigger_gating.py:318-324,623-644` で、いずれも activation/bundle receipt を消費しない。
- 提案: `current generation` と `active generation` を分離し、exact key-set・content-addressedな activation receiptを新設する。floor、oracle、P3、T-126、selector、silo promotionの全入口が、最初の書込み前とreceipt/promotion時に同じ migration epochとbundle SHAを検査する。段4成功後だけ receiptを発行し、自動g1 fallbackは設けない。
- **成果物影響**: 未検証g2がcertified集合へ入り得て、材料レポートが不完全bundleを現行値として参照し、試行台帳には閉鎖区間のg1/g2 entryが混在する。

### 3. `contract-bound` 判定を呼出側が `None` で回避できる

[severity: must-fix]

- 攻撃シナリオ: Pegasus上で一般 `run_campaign(..., env_contract=None)` を呼ぶと、siteを取得した後でも即 `None` を返し、current contract検査を通らない。campaign IDはcontract hashを含まず、pipelineもlegacy経路へ落ちるため、同じcfgのg1/g2測定が同じWAL/layoutを共有する。段2の「current producerは必ずlookup」という不変条件は現入力面では成立しない。
- 根拠: `s2-plan.md:48-50,198-204,327`、`orchestrator/campaign/loop.py:62-75,101-116,139-145`、`orchestrator/campaign/pipeline.py:501-504`、`orchestrator/campaign/ident.py:125-156`
- 提案: contract-bound性をoptional引数の有無で決めず、実siteと「測定するか」から境界内で導出する。Pegasus測定では current contractを内部解決して必須化し、そのhashをlayout生成前にpreimageへ入れる。dry/non-measurementは別の型付きmodeにする。
- **成果物影響**: 試行台帳は同じcampaign ID/WALへg1/g2値を混在させ、certified選択・材料レポートはその台帳を拒否して受理集合を狭めるか、legacy entryを認めて世代分離を失う。

### 4. T-126の実行可能lookupと試行identityが閉包から脱落している

[severity: must-fix]

- 攻撃シナリオ: g2で calibration refだけが変わり、clocks/numactl/attestation/isolationが同じなら、T-126のfield比較は通る。しかしcontrol、series identity、evaluation eventのどこにもcanonical `environment_contract_sha256` や calibration ref がない。現行historical verifierもsource/protocol identityは再計算するが、記録されたcontract→calibration辺を検証しない。
- 根拠: 未列挙のlookupは `orchestrator/qualification/t126_driver.py:496,868`。T-126環境exact-setは `orchestrator/qualification/contract.py:140-149`、series exact-setは同`:454-469`、生成preimageは `t126_driver.py:386-425`、event exact-setは `orchestrator/qualification/artifacts.py:844-867`、historical identity verifierは `orchestrator/qualification/identity.py:112-185`。canonical fingerprintの実定義は `orchestrator/campaign/env_contract.py:145-160`。
- 件数訂正: campaign配下18 callに、T-419 probeの1 call `tools/pegasus/probes/t419_probe_causality.py:3394-3396`、T-126の2 callを加え、production全体は **21 call**。段2の18も親の20も全体値ではない。
- 提案: T-126のcontrol/series/event/receiptをversion upし、canonical contract hash、calibration path/SHA、検証receiptをexact-setへ追加する。historical verifierはhash逆引きで再検証する。T-126の `protocol_sha256` や `env_contract.py` source blob hashを代用品にしない。旧成果物は書き換えない。
- **成果物影響**: T-126は`evidence-only/no-promotion`なのでcertified選択・材料レポートの受理集合は直接変わらないが、試行台帳は各seriesがg1/g2のどちらを測ったか現行verifierで解決できない。

### 5. launch certificate がP3 proof-chain列挙から落ちている

[severity: should-fix]

- 攻撃シナリオ: 設計の `integrity_resolved` 列挙どおりprotocol/journal/receipt/manifestだけをbundle・retention対象にすると、launch certificateが欠落または未解決になる。ratified verifierはcertificateのexact schema、run ID、protocol hashを必須検証し、equality chainにも含めるため、旧full proofは途中で停止する。
- 根拠: `s2-plan.md:291-295` の列挙にcertificateがない。実leafは `orchestrator/campaign/s8b_launch_cert.py:14-23,50-126,129-144`、consumerは `orchestrator/campaign/s8b_ratified_freeze.py:2893-2913`、等式辺は同`:146-155,2937-2964,2997-3002`。
- 提案: launch certificate validatorを `(L)/(G)`、各certificate bytes/path/SHAを `(P)` の独立surfaceとして追加する。bundle/ratified closureにcertificate roleとraw SHAを明記し、欠落・protocol hash変更のmutationを加える。旧certificateは編集しない。
- **成果物影響**: certified floor proofがcertificateで切れ、材料レポートはratified入力を受理できず、試行台帳の `launch_certificate_sha256` がdangling referenceになる。

### 6. selector閉包を `(N)` だけに分類しており、source/pre-oracle実体を落とせる

[severity: should-fix]

- 攻撃シナリオ: namespaceだけ世代対応し、history verifierに通常の `verify_prediction_freeze()` を再利用すると、5つのsource fileの現worktree SHAが将来変わった時点でg1が失格になる。また `pre_oracle_head` のGit object、parser/protocol blob、legacy evidenceのworktree bytesを保持しなければratified historyも解決不能になる。
- 根拠: 段2は当該面を `(N)` のみとする `s2-plan.md:62-70`。実際はsource roleのexact-setとcommit pinを持つ `orchestrator/campaign/s8b_selector_freeze.py:63-76,398-412`、current-worktree照合を行う同`:879-905`、H/worktree bytes一致を要求する `orchestrator/campaign/s8b_ratified_freeze.py:2496-2521`、pre-oracle source/blobを検証する同`:2544-2601` がある。
- 提案: bundle exact-setに5 source role、`pre_oracle_head`、parser/protocol blob、journal、raw、envelopeを明記する。history APIはcurrent-worktree verifierではなくcommit blob経路を使い、pre-oracle commit/Git objectsとlegacy evidence bytesをretention対象にする。
- **成果物影響**: source更新後にg1 certified selector proofが再生不能となり、材料レポートはselector provenanceを確立できず、試行台帳のraw invocation参照も再parse不能になる。

### 7. `FROZEN_MANIFEST` の本文記述が8件のまま

[severity: nit]

- 攻撃シナリオ: 手動閉包監査で設計文書を正本と誤認すると、8件・key-set未検査として移行確認を組み、現在の23件exact key-setを見落とす。
- 根拠: `docs/freeze-permanent-design.md:56-58` は8件・差替え可能と記すが、実装は23件 `orchestrator/tests/test_frozen_artifacts.py:38-85,139-153` かつ独立exact key-set `:87-114`。
- 提案: 当該記述を歴史snapshotと明示するか、現行23件/exact key-setへ訂正する。manifestや旧凍結bytes自体は変更しない。
- **成果物影響**: 現行testがfail-closedなのでcertified選択・材料レポート・試行台帳の値や受理集合は直接変わらないが、移行監査報告の閉包件数が誤る。

既知の二義化については、T-419の `env_contract_sha256` はsource file hash `tools/pegasus/probes/t419_probe_causality.py:3532-3534`、S8cの `evidence_contract_sha256` は別documentのsemantic hash `orchestrator/campaign/s8c_preregistration.py:330-337` であり、段2の除外は正しいです。

## 総括

- **NO-GO** — staging順序とactivation境界を塞いでから裁定へ進めるべき。
- 所見: **must-fix 4 / should-fix 2 / nit 1、計7件**。
- 閉包への新規追加: **8 semantic地点**（T-126 6、launch certificate 1、docs 1）。
- 既存3 surface（loop、selector、ratified proof）は分類・consumer範囲の拡張が必要。
- executable lookup総数は **21**（campaign 18 + T-419 1 + T-126 2）。
- 旧凍結bytesの変更、正しさgateの緩和、g1 fallbackは提案していない。
- 静的検査のみ。pytestは実行せず、緑は主張しない。