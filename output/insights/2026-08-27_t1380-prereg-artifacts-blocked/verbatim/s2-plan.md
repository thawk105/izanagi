## Q1

現状の権威だけでは 3 artifact を正当に発行できない。`master_seed` は導出可能だが、schedule authority の一部、`campaign_id`、attempt-registry genesis の slot 集合が未確定である。値を補えば設計外の発明になるため、本 wave は停止条件に当たる。

### Artifact field の導出表

|field|権威と導出規則|判定|
|---|---|---|
|`trial-manifest.schema_version`|`trial_registry.MANIFEST_SCHEMA_VERSION` (`trial_registry.py:55`)。`load_trial_manifest()` が exact 一致を要求 (`:769-788`)|導出可|
|`trial-manifest.prereg_commit`|artifact 生成コードと検査を導入した anchor commit `A`。内容 commit `P` の親として Git から取得する。これは P 自身ではない (`docs/decisions.md:22436-22444`)|導出可|
|`trial-manifest.trials`|`HOLDOUTS × ARMS` の積を `HOLDOUTS`、次に `ARMS` の順で列挙 (`trial_registry.py:73-74,754-766`; 設計 `phase3-8c-preregistration.md:3,139`)|導出可|
|`trials[*].trial_id`|`f"{holdout.lower()}-{arm}"`。入力は設計済み cell 座標だけで、例は `h1-on`。`[a-z0-9][a-z0-9._-]{0,63}`、一意性を満たす (`trial_registry.py:107,739-751`)|導出可。authority digest の付加は不要|
|`trials[*].arm`|`on/off/swapped` (`phase3-8c-preregistration.md:3,80-87`; `s8c_schedule.py:53`)|導出可|
|`trials[*].holdout`|`H1/H2` (`phase3-8c-preregistration.md:3`; `holdout_freeze.json:39-49,307-315`)|導出可|
|`trials[*].campaign_id`|既存の `_prepare_manifest_campaign_identity()` から `ident.campaign_id()` を使う (`p3_autonomous_workload_trial.py:1143-1186`; `ident.py:150-189`)。独自 hash 規則は既存 production consumer と一致しない (`p3_autonomous_workload_trial.py:1263-1285`)|**導出不能**。site / environment が未確定で、Pegasus では site 値が campaign preimage に入る (`p3_s4_loop_trigger_gating.py:423-437`; §5 解除条件 `phase3-8c-preregistration.md:157-158`)|
|`trials[*].generations`|設計の exact `G=2` (`phase3-8c-preregistration.md:91-95`)。loader も整数 2 だけ受理 (`trial_registry.py:747-748`)|導出可|
|`prereg-effective-binding.schema_version`|`EFFECTIVE_BINDING_SCHEMA_VERSION` (`trial_registry.py:70,1341-1343`)|導出可|
|`prereg_content_commit`|manifest、schedule、genesis を導入した内容 commit `P` の OID|導出可、P 作成後のみ|
|`manifest_path`|要求済み固定 path `output/s8c-preregistration/trial-manifest.v1.json`。P の Git tree から exact blob を読む (`trial_registry.py:1405-1426`)|導出可|
|`manifest_sha256`|P にある manifest raw bytes の SHA-256 (`trial_registry.py:1412-1426`)|導出可|
|`freeze_id`|設計は「freeze identity」を要求するが、condition-freeze tip digest、manifest digest、protected digest のどれかを選ぶ規則がない (`phase3-8b-descriptor-design.md:538-543`; `trial_registry.py:1354-1356`)|**導出不能**。候補の選択は新しい値規則の発明になる|
|`attempt_registry_path`|`DEFAULT_ATTEMPT_REGISTRY_PATH` の固定値 (`trial_registry.py:61-63,1361-1362`)|導出可|
|`attempt_registry_initial_sha256`|P に導入した genesis JSONL bytes の SHA-256 (`trial_registry.py:1427-1438`)|genesis が作れれば導出可。現状は不可|
|`schedule.schema_version`|`SCHEDULE_SCHEMA_VERSION` (`s8c_schedule.py:51,340-345`)|導出可|
|`schedule.generator_version`|`GENERATOR_VERSION` (`s8c_schedule.py:52,340-345`)|導出可|
|`schedule.master_seed`|anchor `A` で `validate_condition_freeze_at(A).tip_record_sha256` をそのまま使う (`s8c_preregistration.py:1714-1720`)。追加 hash や乱数は使わない|導出可|
|`schedule.cells`|`_ordered_cells(master_seed)` (`s8c_schedule.py:286-314,330-339`)|導出可|
|`cells[*].schedule_index`|上記順序の `enumerate()` (`s8c_schedule.py:330-339`)|導出可|
|`cells[*].arm`, `holdout`|上記 ordered product (`s8c_schedule.py:299-314`)|導出可|
|`cells[*].search_space_sha256`|18-field authority の search-space 部分を `search_space_digest()` へ渡す (`s8c_schedule.py:252-272`)|authority 不成立のため現状不可|
|`cells[*].initial_state_sha256`|18-field authority の initial-state 部分を `initial_state_digest()` へ渡す (`s8c_schedule.py:252-278`)|authority 不成立のため現状不可|

### 18 authority field の出所

|authority field|既存の値・導出関数|判定|
|---|---|---|
|`arms`|`s8c_schedule.ARMS` (`s8c_schedule.py:53`)|可|
|`designated_source_context`|`p3_autonomous_workload_trial.DESIGNATED_SOURCE_CONTEXT` (`p3_autonomous_workload_trial.py:357-369`)|値は実在。ただし設計文書自身には exact bytes がない|
|`descriptor_bindings`|各 H1/H2 × arm を `s8c_arm_inputs.resolve_arm_input()` で anchor commit から再解決 (`s8c_arm_inputs.py:434-494`)|値は導出可。mapping の exact JSON 形は未規定|
|`gating_spec`|`GATING_SPEC` (`p3_autonomous_workload_trial.py:322-326`)|値は実在。ただし設計文書に exact bytes はない|
|`holdout_bindings`|`holdout_freeze.json` を `_holdout_bindings_from_freeze()` で射影 (`trial_registry.py:77-102`)|可|
|`holdouts`|`HOLDOUTS` (`s8c_schedule.py:54`)|可|
|`role_contracts`|`ROLE_CONTRACTS` (`p3_autonomous_workload_trial.py:271-320`)|値は実在。ただし設計文書に exact bytes はない|
|`role_files`|`ROLE_FILES` の path と anchor commit の blob bytes (`p3_autonomous_workload_trial.py:261-269`)|**未確定**。path、bytes、hash のどれを authority JSON に置くか規約がない。path だけでは role file 改変を検出できない|
|`role_payload_allowlist`|`ROLE_PAYLOAD_KEY_SPEC` (`p3_autonomous_workload_trial.py:328-355`)|可|
|`workloads`|`FORMAL_WORKLOADS` を通常 JSON mapping へ射影 (`p3_autonomous_workload_trial.py:242-249`)|可|
|`attempt_policy`|`s8c_generation_projection.ATTEMPT_POLICY` (`s8c_generation_projection.py:28-31`)|可|
|`baseline`|`_INITIAL_ROLE_METRICS` から `_role_metric_payloads()`、`_coder_baseline_payload()` (`p3_autonomous_workload_trial.py:145-151,1684-1747`)|値は導出可|
|`descriptor_binding`|runtime では cell ごとに異なる `descriptor_record` (`p3_autonomous_workload_trial.py:2585-2607`)|**導出不能**。schedule は全 cell 共通の単一 mapping を要求するが、実 authority は arm ごとに異なる|
|`gating_snapshot`|`snapshot_gating_spec()` は `GatingSpecSnapshot` を返す (`s8c_generation_projection.py:173-212`)|**未確定**。schedule は JSON object を要求するが、dataclass からの canonical projection が未規定|
|`initial_role_metrics`|`_INITIAL_ROLE_METRICS` (`p3_autonomous_workload_trial.py:145-151`)|可|
|`leakproof_context`|production 値は文字列 `LEAKPROOF_CONTEXT` (`s8c_generation_projection.py:22-26`)|**型不一致**。schedule は JSON object を要求する (`s8c_schedule.py:91-105,237-240`)|
|`stop_policy`|`s8c_generation_projection.STOP_POLICY` (`s8c_generation_projection.py:32-35`)|可|
|`whiteboard`|正式な初期状態は `_whiteboard()` の空配列 (`p3_autonomous_workload_trial.py:1650-1652`)|**型は合うが受理不能**。`validate_authority()` は空配列を拒否する (`s8c_schedule.py:194-207`)|

少なくとも `descriptor_binding`、`leakproof_context`、`whiteboard` は既存の本物の値をそのまま渡しても `validate_authority()` を通らない。`role_files` と `gating_snapshot` も一意な projection がない。P4 は成立しない。

### `master_seed` に対する判断

P1 の方向には賛成する。ただし「発効中の record」ではなく、anchor commit `A` で履歴検証を通った condition-freeze tip record と呼ぶべきである。事前登録全体は §5 未記入かつ 12 predicate 非充足なので「発効中」ではない。

tip record の raw SHA-256 をそのまま seed にすれば、

- 結果非依存で一度だけ決まり、再抽選を必要としない。
- schedule 自身が seed、generator version、cell order、authority digest を持つため、seed 単独を標本束縛と誤認しない (`phase3-8c-preregistration.md:135-138`)。
- §5 の値欄は記入しないため、§5 の解除規約にも反しない (`:164-165`)。

ただし authority 18 field が閉じない現状では schedule はまだ発行できない。

### Attempt-registry genesis

binding を発行するなら genesis は `P` に必須である。loader は P に genesis blob がなければ拒否する (`trial_registry.py:1427-1438`)。

`create_attempt_registry_genesis()` の引数は `repository_root`、manifest path/hash、`freeze_id`、全 slot、closed retry reason、canonical registry pathである (`trial_registry.py:2387-2434`; underlying contract `attempt_registry_core.py:1402-1510`)。現状の問題は次のとおり。

- `freeze_id` の権威規則がない。
- slot は `trial_id/arm/holdout/campaign_id/replicate_index/attempt_index/schedule_row_sha256` を要求する (`trial_registry.py:139-142,1940-1977`)。
- §5 の反復数 `n` は未記入である。6 個の `r0/a0` fixture だけを凍結すると、後から必要になる `n>=2` の slot を append できない (`phase3-8b-descriptor-design.md:464-484,518-543`)。
- retryable reason の現実装値は `trial_registry.py:132-134` にあるが、8b §10.5 が要求する「事前登録の凍結範囲に exact 列挙」が設計文書側にない (`phase3-8b-descriptor-design.md:531-537`)。
- production も現在 `replicate_index == 0` だけを選ぶ (`p3_autonomous_workload_trial.py:1299-1353`)。

したがって P5 は「binding と同時に genesis が必要」という必要性は正しいが、本 wave で正しい genesis を発行できるという実行可能性は誤りである。

## Q2

停止条件を解消した後の commit 構造は次の形にする。

1. `A`: 導出器、純粋 genesis builder、CLI、unit test、負の対照を導入する support commit。manifest の `prereg_commit` はこの `A`。
2. `P`: `trial-manifest.v1.json`、`schedule.v1.json`、`attempt-registry.jsonl` genesis を導入する内容 commit。schedule の出現で変わる C05 gap snapshot と current-artifact 再導出検査もここに置く。
3. `C`: `prereg-effective-binding.v1.json` **だけ**を追加する。親は `P` ただ一つ。`git diff-tree` の path 集合も binding path の singleton として検査する。
4. `R`: 段 7 の worklog、handoff、記録だけを追記する。`C` の親集合は変わらない。
5. 段 9 は main を `R` まで ff-only で進める。merge commit を作らない。

`C` 作成後に `assert_effective_commit_exact_parent(P,C)` を実行する (`trial_registry.py:1219-1245`)。main が進行して fast-forward できなくなった場合は merge/rebase で C を流用せず、新 base 上で `A/P/C` を再構成する。P の OID が変われば binding bytes も必ず再生成する。

全 commit に `docs/ai-provenance.md:8-33` の実際の product/model/reasoning/role trailer を付け、値を推測しない。`A` と、test を含む `P` は Codex author trailer が必要 (`docs/ai-provenance.md:44-55`)。`Co-Authored-By` を使う場合は同じ最終 trailer block に連続配置する (`:14-16`)。

現状は Q1 の停止条件があるため、`A` も作らず author 段へ進めない。

## Q3

停止条件解消後は、anchor commit `A` を固定入力として次を実装する。

- `derive_content(A)`:
  - A の Git blobから設計文書、freeze、role files、実装 authority を読む。
  - manifest、schedule、genesis の canonical bytes を返す。
- `derive_binding(P)`:
  - P の manifest/genesis blobを歴史 bytes として読む。
  - P OID、path、SHA-256 を使って binding bytes を返す。
- `--check --anchor A --content P --effective C`:
  - commit 済み 3 artifact と再導出 bytes を byte 単位で比較する。
  - genesis bytes、C の exact parent、C の singleton diff も検査する。
  - generator module 自身が A の blobと一致することを要求し、後続 commit で導出式だけ差し替える攻撃を拒否する。

負の対照は最低でも次を独立に置く。

- 18 authority field を一つずつ変更し、schedule bytes が変わり、保存済み schedule との check が赤になること。
- condition-freeze tip digest を変更し、埋め込まれる `master_seed` と schedule bytes が変わること。
- holdout、arm、`G=2` のいずれかを変更し、manifest bytes が変わること。
- role file bytesを変更し、path が同じでも schedule digest が変わること。path しか hash しない projection は不採用。
- P の manifestまたは genesisを変更し、binding bytesが変わること。
- C の親を P の祖先や別 commit へ置換し、exact-parent 検査が赤になること。
- 保存 artifact と authority を同時改変する攻撃に対し、A の historical blobsと generator blobを読むことで current-worktree 同時改変を拒否すること。

注意すべき恒真経路は、`validate_authority()` が18 keyの「意味」を検査せず、型と非空性しか検査しない点である (`s8c_schedule.py:210-249`)。そのため fixture 風 mapping を作って `regenerate()` と比較するだけでは D1077 を満たさない。

この check は production launch からは到達不能である。現在の `_load_s8c_schedule_authority()` は無条件に unavailable を送出する (`p3_autonomous_workload_trial.py:1799-1804`)。schedule が存在すれば C05 は production reachability 検査で `schedule-consumer-unreachable` になる (`s8c_preregistration_evidence.py:2156-2185`)。C05 production 配線は指定どおり scope 外であり、「到達済み」とは扱わない。

契約 C03/C08 の manifest field path が `cells[*]` である一方、実 schema は `trials[*]` である (`s8c_preregistration_evidence_contract.v1.json:101-109,307-315`; `trial_registry.py:110-113`)。これは所見として残し、T-1806/C10 field-path 拡張と同様に本 wave では修正しない。

## Q4

### 12 predicate の差分

評価器の control flowに基づく最終状態は次のとおり。

|predicate|発行前|3 artifact 発行後|変化|
|---|---|---|---|
|C01|`EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`|同じ|なし|
|C02|同上|同じ|なし|
|C03|`UNSATISFIED / manifest-registry-proof-undefined`|同じ|なし|
|C04|`EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`|同じ|なし|
|C05|`EVIDENCE_UNDEFINED / schedule-schema-absent`|`UNSATISFIED / schedule-consumer-unreachable`|**status と reason の両方**|
|C06|`EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`|同じ|なし|
|C07|同上|同じ|なし|
|C08|`EVIDENCE_UNDEFINED / prereg-binding-proof-undefined`|同じ|なし|
|C09|`EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`|同じ|なし|
|C10|同上|同じ|なし|
|C11|同上|同じ|なし|
|C12|同上|同じ|なし|

根拠は次のとおり。

- C03/C08 は `machine_checkable=false` で、artifact bytes ではなく registry source形状だけを見る (`s8c_preregistration_evidence.py:1613-1778,1781-1930`)。
- C05 は最初に schedule の有無を見る (`:2082-2088`)。存在後は consumer module検査を通るが、`run_trial` からの required target 3 件がないため `UNSATISFIED` になる (`:2156-2185`)。
- 実 HEADへ scheduleを注入した direct probe の期待値も `UNSATISFIED / schedule-consumer-unreachable` で固定されている (`test_s8c_preregistration_predicates.py:3413-3416`)。
- `SATISFIABLE_CONDITION_IDS` は空集合のまま (`s8c_preregistration_evidence.py:3075`)。

したがって `test_current_repository_gap_reason_snapshot_requires_cross_wave_review` では C05 の1行だけを、`test_s8c_preregistration_predicates.py:283` から新しい status/reasonへ更新する。

`test_current_repository_snapshot_has_zero_satisfied_predicates` (`:229-237`) の充足 0 件は維持される。C05 は `SATISFIED` ではなく `UNSATISFIED` へ移るため、停止条件には当たらない。

### 実 repo reader の全数静的確認

`test_real_repo_serialization.py:51-153` が独立 pin する real-repo reader 92 node と、`output/` 全体を列挙するテストを静的に確認した。

- `test_real_repo_serialization.py:581-611,1019-1038` と `test_s8b_floor_campaign.py:1485-1530` は before/after snapshotであり、既存 file の固定 cardinalityではない。
- T-080 の output copy は Git-visible path を動的に列挙する (`test_s8b_oracle_driver.py:808-835,1028`)。新 file は入力と期待側へ同じく入る。
- `test_s8b_repo_scan_invariant.py:27-35` が pin するのは holdout conjunction hit 集合で、file count ではない。manifest、binding、schedule、genesis は三軸 YCSB 値を持たないため新 hitを作らない。新 derivation codeも既存の invariant検査へ含める必要がある (`test_s8c_preregistration_invariant.py:613-635`)。
- `test_artifact_admission.py:841-851` の exact 32件は `campaign.lock` だけが対象で、新 artifact は一致しない。
- predicate snapshot groupに新しい current-artifact check nodeを足すなら、`test_real_repo_serialization.py:242-246,1257-1274` の独立 goldenと件数も同じ `P` で更新する。

既存テストで、単に `output/` にこれらの file が増えることだけを理由に赤になるものは見つからなかった。

### `FROZEN_MANIFEST`

追加しない。これは全 `output/` file の manifest ではなく、指定された凍結族23件だけの literal pinである (`test_frozen_artifacts.py:41-88,234-248`)。別の独立検査も23件を要求する (`test_s1_9pair_figure_provenance.py:564-580`)。

運用 artifact が condition-freeze namespace 外に存在してよいことは既存テストでも明示されている (`test_s8c_preregistration_core.py:1670-1679`)。3 artifact と genesis を `FROZEN_MANIFEST` に加える必要はない。

pytest は実走していない。read-only 環境で evaluator の直接実行も試みたが、利用可能な一時 directory がなく Git helper が起動できなかったため、緑とは報告しない。上記は実装と既存期待値の静的追跡結果である。

## Q5

第一候補では凍結範囲を変更しない。

- `docs/phase3-8c-preregistration.md` の §1〜§4、§6、§7、§5欄名を編集しない。
- evidence contract、evaluator、`SATISFIABLE_CONDITION_IDS`、`s8c_schedule.validate_authority()` を編集しない。
- artifact の存在による C05 の現在理由変更は evaluator の意味変更ではないため、`DECIDER_VERSION` bumpや新 condition-freeze recordは不要。
- authority type不一致を `validate_authority()` の緩和で通す案は不採用。実施するなら受理意味の変更となり、別裁定、version bump、新世代 recordが必要になる (`phase3-8c-preregistration.md:289-297`)。

§5 の `master_seed` と 6 cell manifest は記入しない。

- `master_seed` は generator、schedule bytes、arm順序を束縛する機構と同じ改訂単位でのみ記入できる (`phase3-8c-preregistration.md:164-165`)。production consumerが到達不能なので解除条件未充足。
- 6 cell manifest欄は arm binding、registry、二段束縛を起動・registry・受入が実際に消費し、事前割当 slotを消費するまで記入できない (`:179-182`)。
- site、environment、正式投入時刻等も未確定である (`:157-158,183`)。

artifact 発行と §5 記入は別である。ただし現状はartifact側にも Q1 の停止条件がある。

## Q6

停止条件解消後に予定する変更面は次のとおり。

既存 file:

- `orchestrator/campaign/trial_registry.py:2387-2434`  
  writerから副作用のない genesis bytes導出関数を抽出し、writerと`--check`が同じ関数を使う。
- `orchestrator/tests/test_trial_registry.py:5643-5695`  
  純粋導出 bytesと実 writer bytesの一致、全 slot、retry理由、newline framingを検査。
- `orchestrator/tests/test_s8c_preregistration_predicates.py:269-300`  
  C05だけを新しい status/reasonへ更新。
- `orchestrator/tests/test_s8c_preregistration_invariant.py:31-43,613-635`  
  新 derivation module、test、artifact、genesisがholdout scanを汚染しないことを検査。
- `orchestrator/tests/test_real_repo_serialization.py:242-246,1257-1274`  
  current-artifact check nodeを既存 snapshot groupへ追加する場合のみ goldenを更新。

新規 file:

- `orchestrator/campaign/s8c_preregistration_artifacts.py`  
  authority commit reader、18-field builder、manifest/schedule/genesis/bindingの純粋導出、CLI `emit-content` / `emit-binding` / `--check`。
- `orchestrator/tests/test_s8c_preregistration_artifacts.py`  
  byte一致、18-field mutation matrix、P/C topology、artifact tamper、authority tamperの負の対照。
- `output/s8c-preregistration/trial-manifest.v1.json`  
  P側 manifest。
- `output/s8c-preregistration/schedule.v1.json`  
  P側 schedule。
- `output/s8c-preregistration/attempt-registry.jsonl`  
  P側 genesis。要求3件外だがbindingの必須依存。
- `output/s8c-preregistration/prereg-effective-binding.v1.json`  
  Cで唯一追加する file。

編集しない file:

- `docs/phase3-8c-preregistration.md`
- `orchestrator/campaign/s8c_schedule.py`
- `orchestrator/campaign/s8c_preregistration_evidence.py`
- evidence contract
- condition-freeze records
- `test_frozen_artifacts.py`

値とcommit OIDが相互依存するため、実装子は分けない方がよい。停止条件解消後に1本の実装子が導出器・artifact・検査を一貫して扱い、親が `A → P → C` のcommit操作だけを担当する。ただし現時点では実装子を起動すべきでない。

## 総括

- **実装可能性:** 現在の権威だけでは実装・発行不可。author段へ進まず停止する。
- **停止条件:** 18-field authority の型・意味不一致、site未確定による`campaign_id`不定、`freeze_id`不定、反復数・attempt数・retry理由未確定によるgenesis slot集合不定。
- **P1:** 賛成。ただし「発効中」ではなく、anchor `A` で検証済みの condition-freeze tip raw digestをそのまま使う。§5は記入しない。
- **P2:** 反対。`trial_id` は cell座標から直接導出できるが、`campaign_id` は独自hashでなく既存`ident.campaign_id()`を使う必要があり、site未確定で現状導出不能。
- **P3:** 賛成。`A`をmanifest anchor、`P`を内容commit、`C`をbinding-only直子とする。
- **P4:** 反対。18 fieldは既存凍結物だけでは組めず、少なくとも`descriptor_binding`、`leakproof_context`、`whiteboard`が現 schemaと矛盾する。
- **P5:** 必要性には賛成、現 waveでの発行には反対。genesisはbindingに必須だが、正しい閉じたslot集合をまだ導出できない。