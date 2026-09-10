## 所見

1. **blocker — 狙う best-of-N の生きた formal 経路が特定されていない。** `plan-v1.md:25-30` 自身が、同一 repository では canonical genesis、全 ref 履歴、P blob、manifest の一致により第二の formal receipt 経路がないと確認している。実コードも第二 root を拒否し (`orchestrator/campaign/trial_registry.py:2510-2561`)、formal acceptance で genesis と manifest を完全一致させる (`orchestrator/campaign/trial_registry.py:3455-3509`)。残る独立 repository 経路は計画の対象外である (`orchestrator/campaign/trial_registry.py:4457-4461`)。  
   放置時: 同一 repository の best-of-N 受理集合は変更前後で変わらず、独立 repository を使う実在経路も残る。

2. **blocker — 検査が downstream verifier まで届かない。** 計画は issuer 内だけで全件検査し、outer receipt schema と verifier を変更しない (`plan-v1.md:104-108,148,168`)。v4 receipt の参照集合には attempt registry がなく (`orchestrator/campaign/s8c_acceptance_receipt.py:45-67`)、verifier が再検査するのも manifest、trial registry、lifecycle だけである (`orchestrator/campaign/s8c_acceptance_receipt.py:1117-1160`)。  
   放置時: attempt registry が欠落または未完了でも、対応する v4 receipt を直接構成して HEAD に置けば `VerifiedAcceptanceReceipt` の受理集合へ入る。現時点の certified Layer3 は常に拒否するため (`orchestrator/campaign/layer3_report.py:691-703`)、現在の certified 集合は空のままだが、D1269 の downstream 保証は成立しない。

3. **blocker — v3 genesis の production producer がない。** `create_attempt_registry_genesis` の caller は全てテストで production は 0 件 (`plan-v1.md:124-133`)。production run は既存 registry を読み、slot を予約するだけである (`orchestrator/campaign/p3_autonomous_workload_trial.py:1322-1358`)。CLI にも `register` と `accept` しかない (`orchestrator/campaign/trial_registry.py:6287-6354`)。  
   放置時: 通常の production 経路は `prereg_generation` 付き genesis を一件も生成せず、out-of-band の Python 呼出しがない限り formal run は開始できない。

4. **blocker — `not-consumed` を含む正例は receipt 発行まで到達できない。** 計画は三種の final status の混在を正例とする (`plan-v1.md:114-117,154`)。しかし core は `not-consumed.report_sha256` を必ず `None` にする (`orchestrator/campaign/attempt_registry_core.py:977-983`; production 投影も `orchestrator/campaign/p3_autonomous_workload_trial.py:4194-4207`) 一方、acceptance は全 report について terminal の report hash と実ファイル hash の一致を無条件に要求する (`orchestrator/campaign/trial_registry.py:3517-3548`)。  
   放置時: bad side の `not-consumed` receipt を outer receipt に列挙できず、良い結果側だけが発行可能になるため、D1269 が閉じたい選択性が残る。

5. **must-fix — 提案された負例は新 helper を空実装しても赤になる。** 欠落は既存の exact 6 report と terminal 照合で拒否される (`orchestrator/campaign/trial_registry.py:5685-5686,1622-1639,3527-3529`)。余剰と別世代混入は core の undeclared-slot 照合で拒否され (`orchestrator/campaign/attempt_registry_core.py:539-584`)、空集合は既存 genesis gate で拒否される (`orchestrator/campaign/attempt_registry_core.py:483-503`)。これらが計画の主要負例である (`plan-v1.md:155-159`)。  
   放置時: `_assert_predeclared_slot_consumption` の呼出しを削除または空実装してもテストが通り得るため、成果物の受理集合が再び広がっても検出できない。

6. **must-fix — 「承認 artifact」の要件を未解決のまま実装へ進めている。** 現行 8c は承認 command、承認 record、active pointer を明示的に採用しておらず (`docs/phase3-8c-preregistration.md:300-311`)、receipt も approval authority 不在を必須にする (`orchestrator/campaign/s8c_acceptance_receipt.py:420-428`)。genesis creator は渡された slot を固定するだけで、承認を検査しない (`orchestrator/campaign/trial_registry.py:2411-2448`)。  
   放置時: slot/count は固定されても「承認された集合」にはならず、未承認 genesis も formal issuer の入力候補に残る。

7. **must-fix — 変更影響のテスト inventory が不足している。** 計画の更新対象 (`plan-v1.md:150-152`) に `test_attempt_registry_core_s8b_profile.py` がない。同ファイルは v2 genesis bytes と generation 無し slot を exact 比較し (`orchestrator/tests/test_attempt_registry_core_s8b_profile.py:511-552`)、formal/compatibility facade の署名一致も要求する (`orchestrator/tests/test_attempt_registry_core_s8b_profile.py:1980-1988`)。  
   放置時: schema v3 化と formal-only 引数追加により既存テストが失敗し、または安全な署名対称性を根拠なく削ることになる。

8. **nit — `prereg_generation` を全 event と classification receipt へ複製するのは過剰。** 計画は六種の row へ field を追加する (`plan-v1.md:48-53`)。既存 core は一意な `slot_id` から genesis slot を解決し (`orchestrator/campaign/attempt_registry_core.py:539-584`)、capability digest は slot 全体を束縛する (`orchestrator/campaign/trial_registry.py:2182-2203`)。  
   放置時: 受理集合を狭めずに event bytes、chain hash、classification receipt hash、fixture の変更面だけが増える。

## 穴は塞がるか

**部分的。** v3 genesis が実在し formal issuer まで到達するという前提では、activation report の generation と genesis の明示 field の不一致は拒否できる。ただし、同一 repository の path 面と commit 面は変更前から既に塞がっており、この部分は best-of-N の純増防壁ではない。

残る経路は次のとおり。

1. 選んだ側の manifest、trial registry、lifecycle、report だけを用意する。
2. attempt registry を参照しない正規形 v4 receipt を canonical path に置いて commit する。
3. `verify_acceptance_receipt` を呼ぶ。検査対象に attempt registry がないため、issuer の新 helper を一度も通らず verified receipt が得られる。
4. 現時点では `certifying=false` により Layer3 が止めるが、receipt を材料として使う downstream には全 slot/count/generation の証拠が渡らない。

さらに、独立 clone を N 個作り、各 clone で一つずつ canonical genesis と receipt を発行して良い側だけを渡す経路は残る。各 repository 内の履歴検査は通り、計画はこの経路を明示的に対象外としている。

個数は issuer 内では固定される。manifest は exact 6 件 (`orchestrator/campaign/trial_registry.py:743-790`)、initial slot はそれと一致し (`orchestrator/campaign/trial_registry.py:3495-3509`)、同一 series の重複 attempt 0 は拒否される (`orchestrator/campaign/attempt_registry_core.py:483-503`)。ただし、その個数は outer receipt と downstream verifierには束縛されない。

## 最小形を超えている部分

- start、pre-observation-seal、classification、observation-start、terminal、classification receipt の全てへ `prereg_generation` を複製する部分は削れる。genesis slot、capability digest、downstream 用の固定 projectionまたはattempt-registry prefix参照で足りる。
- 現行 production acceptance だけを対象とする全件 helper は、exact 6 reports、manifest一致、terminal照合と重複する。issuer の防御として残す場合も、主たる検査場所は outer receipt verifier に移すべきである。
- 全世代台帳、revocation、expiry、check registry、汎用 core への一般化は混ざっていない。
- plan が「最小形を超える」とした outer receipt schema 更新は、実際には downstream 検査を成立させる最小要件であり、削る対象ではない。

## 呼び出し元の検算

参照関係を module alias (`R`、`registry`、`A.trial_registry`) とローカル名まで追った結果、直接 caller 数の差はない。

| 対象 | plan v1 | 検算 | 差 |
|---|---:|---:|---:|
| `create_attempt_registry_genesis` wrapper | 10、全て test | 10、全て test | 0 |
| `assert_formal_attempt_registry_acceptance` | 2 | 2 | 0 |
| `assert_trial_registry_acceptance` | 15 | 15 | 0 |
| `_reserve_registered_attempt_slot` | production 1 | production 1 (`p3_autonomous_workload_trial.py:4563`) | 0 |

ただし、直接 caller 数は変更影響の総数ではない。`_S8C_ATTEMPT_PROFILE` を lower-level core に渡すテストが `orchestrator/tests/test_attempt_registry_core_s8b_profile.py:511-554` にあり、v3 slot/schema の影響を受けるが plan の更新対象から落ちている。

production genesis caller が 0 件という事実は重大である。producer 側変更は現物 artifact を変えず、consumer 側だけを厳しくして formal 経路を到達不能にする。

## 親 brief の誤り

- **A1 は過大評価。** creator 自体が検査するのは非空、slot ID 一意、attempt index 連続性であり (`orchestrator/campaign/attempt_registry_core.py:483-509`)、manifest に対する完全性は後段 acceptance (`orchestrator/campaign/trial_registry.py:3495-3509`) で初めて検査される。
- **A3 の root exact key 集合は不完全。** 実際には `schema_version`、`event`、`freeze_id`、`manifest_path` などを含み、v2 は chain fields も持つ (`orchestrator/campaign/trial_registry.py:140-171`)。
- **A7 の「同一」は誤り。** §7 の穴は未登録 run、別 `--run-root`、report 前 crash を含む (`docs/phase3-8c-preregistration.md:497-501`)。単一 canonical formal genesis の generation 欠落だけとは一致しない。
- **A9 は文字列検索としては正しいが、機能評価として誤り。** dedicated helper はなくても、exact manifest reports、initial genesis set、report-terminal 照合の合成により現行 replicate 0 の六系列は既に全件 final を要求される (`orchestrator/campaign/trial_registry.py:1622-1639,3495-3529,5685-5686`)。
- **P1 は誤りだが、plan の代案も literal な承認 artifact ではない。** condition freeze は generation の出所、genesis は slot/count の正本だが、現行には承認 authority 自体がない (`docs/phase3-8c-preregistration.md:300-311`)。
- **P2 は同一 repository の formal 経路について誤り。** plan v1 の反証が正しい。実在する残余は独立 repository と未登録 run であり、plan は両方とも閉じない。
- **P3 は政策としては妥当だが、現行 artifact 契約と不整合。** `not-consumed` は report hash を持てないため、outer receipt 発行まで運べない (`orchestrator/campaign/attempt_registry_core.py:977-983`; `orchestrator/campaign/trial_registry.py:3547-3548`)。
- **P4 は支持できる。** generation は activation report から独立に得られ (`orchestrator/campaign/s8c_preregistration.py:1957-1961`)、g1..g13 の既存 bytes を変更する必要はない。
- A2、A4、A5、A6、A8、A10 に実質的な誤りは見つからない。

## 総括

plan v1 は generation の明示束縛としては成立するが、D1269 の best-of-N 防壁としては不十分である。  
同一 repository の formal 経路は既に閉じており、残る独立 repository 経路は対象外のままである。  
さらに production genesis producer がなく、downstream verifier は attempt registry を参照しない。  
`not-consumed` を outer receipt に運べないため、失敗側も全件報告する正例は実現不能である。  
最小修正は genesis の generation 束縛に加え、attempt prefixとslot projectionを outer receiptへ固定し、verifierで再検査する形である。  
pytest は制約に従い実行していない。