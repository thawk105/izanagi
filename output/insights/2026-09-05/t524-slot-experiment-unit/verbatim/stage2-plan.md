## 現状の実測

「承認 artifact」は単一ファイルではない。最小の実体は次の3点である。

- 条件凍結 record は `generation_number` を持つが、slot 宣言を持たない。schema の exact keys は `orchestrator/campaign/s8c_preregistration.py:81-98`、生成番号の導出は同 `:1957-1961`。また、都度の承認 record や active pointer を明示的に採らない設計である (`docs/phase3-8c-preregistration.md:300-315`)。
- 6 cell の論理 universe は trial manifest v2 が固定する。root/trial keys は `orchestrator/campaign/trial_registry.py:55,114-121`、exact 6 件と H1/H2 × 3 arm は同 `:743-790`。
- 全 attempt slot とその個数を直接固定している artifact は attempt registry genesis である。root/slot keys は同 `:140-147`、空集合・重複・不連続 attempt を拒否する処理は `orchestrator/campaign/attempt_registry_core.py:483-509`、canonical path への create-only 発行は `orchestrator/campaign/trial_registry.py:2355-2458`。
- genesis は内容 commit P に置かれ、発効 binding C が canonical path と初期 bytes hash を束縛する (`orchestrator/campaign/trial_registry.py:122-126,295-310,1355-1396,1451-1462`)。従って、D1269 の最小形で slot 宣言を所有させる場所は条件凍結 record ではなく、P 側 genesis である。条件凍結は `prereg_generation` の期待値だけを供給する。

`create_attempt_registry_genesis` が既に固定するものは、非空の slot 全集合、`slot_id`、trial/arm/holdout/campaign、`replicate_index`、`attempt_index`、schedule hash、retry 理由の exact 集合である (`orchestrator/campaign/trial_registry.py:144-147,1954-2001,2411-2448`)。固定していないのは prereg 条件世代である。また、各 slot が消費済みかは genesis 作成時には当然固定せず、acceptance でも全件検査していない。

現行 acceptance は次の境界まで実装済みである。

- manifest と genesis の初期 slot は `(trial_id, arm, holdout, campaign_id, replicate_index=0)` で完全一致させる (`orchestrator/campaign/trial_registry.py:3495-3509`)。従って現状では `replicate_index=1` を足すと受理集合外になる。
- attempt state machine は未宣言 slot、二重 start、二重 terminal、retry 順序違反を拒否する (`orchestrator/campaign/attempt_registry_core.py:556-584,1073-1119,1215-1290`)。
- しかし formal acceptance は、渡された `report_paths` に対応する terminal だけを照合し、全 predeclared unit に final terminal があることは要求しない (`orchestrator/campaign/trial_registry.py:3510-3570`)。core replay も全 slot の終端集合を比較せず、そのまま rows を返す (`orchestrator/campaign/attempt_registry_core.py:986-1010,1290-1333`)。

消費の終端証拠は attempt registry の `event="terminal"` row である。これは slot、classification receipt、raw output、report/observation、status を束縛する (`orchestrator/campaign/trial_registry.py:190-197`)。status の意味は次のとおりである。

- `observed`、`terminal-failure`、`not-consumed` は replicate unit の final consumption と数える。
- `retryable-failure` は次の事前割当 attempt を開く中間終端であり、単独では replicate unit の final consumption と数えない (`orchestrator/campaign/attempt_registry_core.py:1085-1119`)。
- failure/reject を含める根拠は、lifecycle が `complete/partial/indeterminate` をそれぞれ `observed/terminal-failure/not-consumed` へ対応させていることにある (`orchestrator/campaign/trial_registry.py:4853-4859`)。
- classification receipt 自体の存在、bytes、hash、capability binding は既に全 classification row について検査される (`orchestrator/campaign/trial_registry.py:2257-2339`)。

best-of-N の実在経路は、親 brief の記述より狭い。

- trial registry は異なる manifest を複数追記できる。uniqueness は manifest/P/C/trial/campaign の再利用だけを拒否する (`orchestrator/campaign/trial_registry.py:911-933`)。その正例も `orchestrator/tests/test_trial_registry.py:1606-1623` にある。
- ただし formal acceptance は canonical attempt root の manifest hash と初期 P blobを要求する (`orchestrator/campaign/trial_registry.py:3455-3494`)。canonical path と全 ref 上の第二 root も拒否する (`orchestrator/campaign/trial_registry.py:2510-2561`)。従って、同一 repository 内で複数 manifest のうち好きな1件を現在の formal issuerへ通す path面・commit面の経路は見つからない。
- 開いているのは世代面の意味束縛である。activation report は freeze generation を導出するが (`orchestrator/campaign/s8c_preregistration.py:1957-1961`)、attempt slot keysにも acceptance receipt trial keysにもその値がない (`orchestrator/campaign/trial_registry.py:144-147`; `orchestrator/campaign/s8c_acceptance_receipt.py:68-87`)。
- 独立 clone/repository は現行の単一 repository 履歴検査の外である。同様の限界は lifecycle 側でも明記されている (`orchestrator/campaign/trial_registry.py:4457-4461`)。これは全世代一般化なしでは閉じない。
- 現行 acceptance receipt は常に non-certifying で (`orchestrator/campaign/s8c_acceptance_receipt.py:33-39,420-428`)、certifying Layer3 consumer は存在しないと明記されている (`orchestrator/campaign/layer3_report.py:682-703`)。

親の provisional 判断は次のとおり。

| 前提 | 判定 | 実測 |
|---|---|---|
| P1 | 反証 | 条件凍結は generation の出所であって slot artifact ではない。slot/count の正本は P 側 attempt genesis、anchor は C binding、cell universe は manifest にまたがる。 |
| P2 | 反証 | 同一 repository の formal pathでは第二 genesisと別 manifest選択は止まる。残るのは明示的 generation field の欠落と、scope外の独立 repository 面である。 |
| P3 | 支持、ただし精密化 | failure/reject も消費に数える。ただし `retryable-failure` は中間であり、各 replicate series の final statusを1件要求する。 |
| P4 | 支持 | generation は既存 activation reportから取得できるため、g1..g13や条件凍結 schemaを変更せず実装できる。 |

静的検査のみ実施した。pytest は実行していない。`git diff --stat` と `git status --short` はともに空で、書き込みはしていない。

## 変更案

変更対象の中心は `orchestrator/campaign/trial_registry.py` とする。`attempt_registry_core.py` は汎用化しない。

1. `orchestrator/campaign/trial_registry.py:64-197`

   - current attempt schema を `p3-8c-attempt-registry/v3` へ上げる。
   - v1/v2 の既存 exact key tableは読取用として保持し、v3 slotだけに必須 field `prereg_generation` を追加する。
   - v3 の start、pre-observation-seal、classification、observation-start、terminal、classification receiptにも `prereg_generation` を入れる。
   - `replicate_slot` という重複 fieldは新設せず、既存 `replicate_index` を D1269 の `replicate_slot` の保存名として使う。LLM探索世代の `generation` / `source_generation` (`orchestrator/campaign/s8c_generation_projection.py:458-500`) とは交差させない。
   - `slot_count` も新設しない。canonical `slots` arrayと、その `attempt_index==0` の件数が唯一の個数正本になる。

2. `orchestrator/campaign/trial_registry.py:1954-2071`

   - `_attempt_slot_config` の series keyを `(prereg_generation, trial_id, arm, holdout, campaign_id, replicate_index)` にする。`attempt_index` は引き続き series内 retry番号とする。
   - `_parse_attempt_slot` は v3 の `prereg_generation` に exact intかつ1以上を要求する。bool、0、負数、欠落を拒否する。
   - capability digestにも `prereg_generation` を含め、別 prereg 世代の receiptを同じ `slot_id` へ移せないようにする。
   - `AttemptSlotCapability` (`:423-450`) に同 fieldを追加し、生成・再検査 (`:2975-3078`) まで運ぶ。
   - v1/v2 replayでは field欠落を旧形として読むが、formal issuerには渡さない。新しい互換層は作らない。

3. `orchestrator/campaign/trial_registry.py:2411-2458`

   `create_attempt_registry_genesis` の署名を次の形へ変更する。

   ```python
   def create_attempt_registry_genesis(
       *,
       repository_root: Path,
       manifest_path: Path,
       manifest_sha256: str,
       freeze_id: str,
       prereg_generation: int,
       slots: Sequence[Mapping[str, Any]],
       ...,
   ) -> Path:
   ```

   `prereg_generation` は必須引数とし、各 slot の同名 fieldとexact一致させる。slot側に自動補完する経路は作らない。これによりschedule producerが同 fieldを含めてschedule hashを作る責任を保持する。

4. `orchestrator/campaign/trial_registry.py:3437-3616`

   次のS8C専用helperを追加する。

   ```python
   def _assert_predeclared_slot_consumption(
       rows: Sequence[Mapping[str, Any]],
       *,
       prereg_generation: int,
   ) -> None:
   ```

   - 期待集合は genesis の `attempt_index==0` だけから、`(prereg_generation, holdout, arm, replicate_index)` として作る。
   - 実績集合は terminal rowsのうち statusが `observed`、`terminal-failure`、`not-consumed` のものから作る。
   - `retryable-failure` は実績 final集合へ入れない。
   - 期待集合が空なら即拒否する。
   - 期待と実績の件数および集合を両方向で完全一致させる。
   - `primary_value` やfitnessは一切読まない。

   `assert_formal_attempt_registry_acceptance` の署名へ必須 `prereg_generation: int` を追加し、既存 strict replay後、report照合前にこのhelperを呼ぶ。compatibility用 `assert_attempt_registry_acceptance` は既存の受理形を維持するが、formal receipt発行には使わない。

5. `orchestrator/campaign/trial_registry.py:5675-5739,6108-6131`

   `assert_trial_registry_acceptance` が持つ `effective_preregistration.report.freeze_generation` を独立の期待値としてformal helperへ渡す。`None`、bool、0以下は拒否する。期待集合をterminal rowsやouter receiptから導出しない。

   outer acceptance receiptの発行は従来どおり全検査後の `:6256-6261` に置く。最小形では `s8c_acceptance_receipt` schemaを上げず、formal issuerが全列挙検査を通過した場合だけreceiptを発行する。

追加する拒否分岐と通る正例は次のとおり。

| 拒否分岐 | 拒否する形 | 通る正例 |
|---|---|---|
| `attempt-registry-schema` | v3 slotの `prereg_generation` 欠落、bool、0、負数 | 全slotが exact int `13` |
| `attempt-prereg-generation` | genesis slotの値がformal consumerへ渡されたgenerationと不一致 | activation reportが13、全genesis slotも13 |
| `attempt-consumption-empty` | predeclared unit集合が空 | H1/H2 × on/off/swapped × replicate 0 の6件 |
| `attempt-consumption-set` | final terminalの欠落、余剰、重複、別世代混入 | 6 unitすべてに1件の final terminal。statusは `observed`、`terminal-failure`、`not-consumed` の混在可 |
| 既存 `attempt-slot` | genesis外のslot/receipt | 宣言済みslotだけを参照するterminal |
| 既存 `attempt-terminal` | 同一attemptのterminal重複 | 各attemptに高々1件 |
| 既存 `attempt-slot-order` | success後retry、順序飛ばし | `retryable-failure` の直後の同一series次attemptだけ |

manifestのexact 6件、replicate 0、arm/holdout productは変更しない (`orchestrator/campaign/trial_registry.py:751-790,3504-3509`)。従って既存の受理集合を任意のreplicate数へ広げない。

## 呼び出し元への影響

`create_attempt_registry_genesis` の直接呼び出し元は10件で、すべてテストである。production callerは0件である。

- `orchestrator/tests/test_attempt_registry_core_equivalence.py:382,545,585,651`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py:7035`
- `orchestrator/tests/test_reflux_origin_binding.py:338`
- `orchestrator/tests/test_trial_registry.py:255,5793,6141,6395`

これらへ `prereg_generation` を追加し、slot fixtureとschedule hash preimageにも同 fieldを加える。v3 differential fixtureは `orchestrator/tests/test_attempt_registry_core_equivalence.py:19,35-38` を追随させる。

`assert_formal_attempt_registry_acceptance` の直接呼び出し元は2件である。

- production内部: `orchestrator/campaign/trial_registry.py:6112`
- test: `orchestrator/tests/test_trial_registry.py:7251`

`assert_trial_registry_acceptance` は署名を変えないが、formal completenessが純増するため、既存の直接呼び出し15件すべてが挙動影響を受ける。

- production CLI: `orchestrator/campaign/trial_registry.py:6348`
- compatibility test: `orchestrator/tests/test_reflux_originless_compatibility.py:75`
- registry tests13件: `orchestrator/tests/test_trial_registry.py:2620,2663,2695,2727,2757,2791,2863,3278,4390,4427,7304,7370,7479`

production run側の `_reserve_registered_attempt_slot` は `orchestrator/campaign/p3_autonomous_workload_trial.py:1299-1370` の1経路だけである。現行どおりreplicate 0を選ぶため署名変更は不要だが、返る `AttemptSlotCapability` に `prereg_generation` が増える。

`verify_acceptance_receipt` のproduction内部 callerは `require_current_verified_receipt` の1件 (`orchestrator/campaign/s8c_acceptance_receipt.py:1230-1243`) である。最小案ではここへattempt registry再検査を足さない。

## テスト案

新しい正負例は `orchestrator/tests/test_trial_registry.py` に追加する。共通 schema/fixture更新は `orchestrator/tests/test_attempt_registry_core_equivalence.py`、`orchestrator/tests/test_p3_autonomous_workload_trial.py`、`orchestrator/tests/test_reflux_origin_binding.py` に行う。

- 正例: `prereg_generation=13`、6個のreplicate 0 unitをgenesisで宣言し、各unitにfinal terminalを1件ずつ作る。`observed`、`terminal-failure`、`not-consumed` を混在させても `assert_trial_registry_acceptance` がreceipt発行まで到達することを検査する。既存正例 `orchestrator/tests/test_trial_registry.py:1651-1741` を拡張してもよい。
- 欠落: 6 unitを宣言したまま1 unitのfinal terminalを作らず、`attempt-consumption-set` で拒否され、acceptance receiptが作られないことを検査する。
- 余剰: genesis外tupleを持つv3 terminal rowを混入し、既存 `attempt-slot` または新しいset比較で拒否されることを検査する。期待集合はgenesisから取り、terminal側から拡張しない。
- 別世代の混入: genesisと期待generationを13に固定し、1件のclassification/terminal receiptだけを14へ変えてhash chainを再計算する。undeclared slotまたはgeneration mismatchとして拒否されることを検査する。
- 空集合: `slots=[]` のgenesis作成が既存非空gateで拒否されることに加え、consumption helper単体にも空のpredeclared集合を与え、全称量化で成功しないことを検査する。
- schema境界: v1/v2は既存read/replay用途では読めるが、`prereg_generation` を持たないため新規formal receipt発行には使えないことを正負対で固定する。
- 不変確認: extra replicate 1が引き続き `genesis initial slot set differs from manifest trials` で拒否される既存テスト `orchestrator/tests/test_trial_registry.py:7566-7596` を維持する。

pytestは実行条件に従い未実行とする。実測結果を緑とは報告しない。

## 親の裁定が要る点

- 「承認 artifact」を人間承認 artifactの意味で使うなら、現行設計と衝突する。8cは承認 record/active pointerを採らず (`docs/phase3-8c-preregistration.md:300-315`)、outer receiptも `t468-approval-authority-absent` を必須とする (`orchestrator/campaign/s8c_acceptance_receipt.py:33-39`)。上記案は「P/Cで固定された事前登録 artifact」という意味であり、人間承認 authorityは新設しない。文字どおりの承認を要求するなら親裁定が要る。
- `replicate_index>0` を今回受理したい場合は親裁定が要る。現行 acceptanceはreplicate 0だけを受理し (`orchestrator/campaign/trial_registry.py:3504-3509`)、production selectorも0へ固定されている (`orchestrator/campaign/p3_autonomous_workload_trial.py:1330-1340`)。広げると既存受理集合が増えるため、本案には含めない。
- `s8c_acceptance_receipt.verify_acceptance_receipt` 自身にも独立再検査を要求するなら、outer receipt v5へattempt registry path/prefix/slot projectionを追加する設計が必要になる。現行 verifierはmanifest、trial registry、lifecycleだけを再検査し (`orchestrator/campaign/s8c_acceptance_receipt.py:1151-1160`)、attempt registryを参照しない。これは最小案を超えるので親裁定へ返す。
- 独立clone/repositoryを跨ぐbest-of-Nまで閉じるのは、唯一のrootを全世代で管理する一般化になるため対象外とする。
- P1とP2は現物と食い違う。P1は反証、P2も同一repositoryのformal経路について反証である。この差を無視して条件凍結recordへslot配列を足す案は採らない。
- condition freezeの判定器、契約本文、evidence evaluatorは変更しないためg14は不要である。これらへ手を入れる案へ変わる場合は、`docs/phase3-8c-preregistration.md:317-323` に従う新世代が必要になる。

## 総括

最小形は、P側attempt genesisへ `prereg_generation` を加え、formal issuerで全replicate unitのfinal terminal集合を完全一致させる形なら実装可能である。  
期待集合はgenesis、期待generationはactivation reportから取り、receipt側から導出しない。  
既存g1..g13、性能値分岐、汎用core、outer receipt schemaは変更しない。  
failureとnot-consumedも消費に数え、retryable-failureだけを中間扱いにする。  
最大のriskは、「承認 artifact」が現行には人間承認 authorityとして存在しない点と、replicate 1以上を受理すると既存受理集合を広げる点である。