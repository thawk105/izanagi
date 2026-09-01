## 前提の実測

- [実測] 指定 9 文書を順番どおり読了した。current HEAD は `e1e53d7db19bd3911797ed1f9699d1ea0e3c8141`、worktree は clean である。sandbox は read-only のため pytest は実行しておらず、以下は静的検査に基づく。`brief-v2.md:1-166`

- [実測] 現台帳は `floor-attempt-registries/{freeze_sha256}/registry.jsonl` で世代次元がない。path 導出は `_relative_registry_path`、`_entry_paths`、`registry_path` に集約されている。`orchestrator/campaign/s8b_attempt_profile.py:378-386`, `orchestrator/campaign/s8b_attempt_registry.py:451-491`

- [実測] current slot identity は `(freeze_holdout_key, configuration_id, repetition, attempt_ordinal)`、series は先頭 3 軸、budget は先頭 2 軸である。legacy campaign の retry ordinal は cell-wide なので、この `attempt_ordinal` へ直写しできない。`orchestrator/campaign/s8b_attempt_profile.py:27-40,121-143,405-408`, `orchestrator/campaign/s8b_floor_campaign.py:5886-5907,6169-6187`

- [実測] registry schema は v1 のみ、retryable reason は空であり、ordinal 1 以後は直前の `retryable-failure` または recovery がないと開始できない。`orchestrator/campaign/s8b_attempt_profile.py:22,367-395`, `orchestrator/campaign/attempt_registry_core.py:1081-1119`

- [実測] core replay は profile の cap と recovery policy digest を genesis に完全一致させるため、一つの current profile で異なる旧世代を replay する案は成立しない。`orchestrator/campaign/attempt_registry_core.py:654-725,986-1020`

- [実測] mutation は共有 admission root の同一 `ledger.lock` を排他取得し、read-only 側には同じ inode の shared lock がある。新しい lock は不要だが、世代列挙と全世代 replay は同じ区間に入れる必要がある。`orchestrator/campaign/s8b_holdout_admission.py:545-638`, `orchestrator/campaign/s8b_attempt_registry.py:984-1048`

- [実測] classification claim address は freeze と slot だけから導出され、payload にも protocol/schedule binding がない。第 2 protocol 世代で同じ slot を使うと create-only claim が衝突する。`orchestrator/campaign/s8b_attempt_registry.py:811-901,1401-1437`

- [実測] `CellHoldoutAdmission` は claim digest を公開せず、値は `_CellState.measurement_generation_claim_digest` にだけある。current marker は `measurement-generation-consumed` の current schemaだが、adapter は legacy `consumed` path と v1 key集合を独自に読む。`orchestrator/campaign/s8b_holdout_admission.py:250-259,390-403,1793-1819,4435-4489,4519-4546`, `orchestrator/campaign/s8b_attempt_registry.py:55-68,1458-1509`

- [実測] `_run_session` は session-start を fsync した後、campaign-owned pre-probe で競合を検出すると `measure_fn` 前に早期終了する。launcher は現在 capture 後の post-probe しか所有しない。`orchestrator/campaign/s8b_floor_campaign.py:5995-6036`, `orchestrator/campaign/s8b_floor_attempt_launcher.py:238-295,548-645`

- [実測] launcher は registry terminal を永続化してから campaign へ戻るが、terminal row は session record 本体を持たない。現状のまま crash すると、journal へ欠けた session bytesを再構成できない。`orchestrator/campaign/s8b_floor_attempt_launcher.py:628-645`, `orchestrator/campaign/attempt_registry_core.py:1814-1897`, `orchestrator/campaign/s8b_floor_campaign.py:6128-6165`

- [実測] result は v4 の単一定数である。pure verifier、live wrapper、candidate、ratified reverify に加え、`_official_earlier_floor_results` が earlier result を選択へ利用する。`orchestrator/campaign/s8b_floor_contract.py:29-38,81-87,157-166`, `orchestrator/campaign/s8b_floor_stats.py:682-768,1036-1082`, `orchestrator/campaign/s8b_holdout_freeze.py:1417-1643,1813-1925`, `orchestrator/campaign/s8b_ratified_freeze.py:2333-2390,3253-3302`

- [実測] 前回説明の訂正は次のとおりである。実名は `append_production_emitter_g2()`、`test_pure_verifier_rejects_legacy_result_schema` は v4 を v3 に変える拒否 test、launcher test caller は public 1 件、private 5 件である。`orchestrator/tests/test_s8b_ratified_freeze.py:1202`, `orchestrator/tests/test_s8b_floor_stats.py:1321-1325`, `orchestrator/tests/test_s8b_floor_attempt_launcher.py:317,393,436,486,626,664`

## 推奨プラン

### 単位 A: 台帳層

- [推測] registry schema を `s8b-floor-attempt-registry/v2` に上げ、v1/v2 readable profile を持つ。v2 path は次で固定する。`orchestrator/campaign/s8b_attempt_profile.py:22,367-386`

  ```text
  floor-attempt-registries/{freeze_sha256}/{protocol_sha256}/registry.jsonl
  ```

- [推測] path API を `_relative_registry_path(freeze_sha256, protocol_sha256)`、`_entry_paths(..., freeze_sha256, protocol_sha256, requested_registry_path=None)`、`registry_path(..., freeze_sha256, protocol_sha256)` に変更する。全内部 call site は `_AttemptState.binding` または引数の binding から protocol digest を得る。`orchestrator/campaign/s8b_attempt_registry.py:451-506,1066-1105,1147-1150,1521-1524,1634-1636,1684-1687,1739-1741,1826-1829`

- [推測] adapter に `_registry_generation_paths_locked(root, freeze_sha256)` を置く。freeze directory 直下で lowercase 64 hex 名の non-symlink real directoryだけを protocol 世代とし、内部の `registry.jsonl` は no-follow regular fileを要求する。通常 sibling fileは無視し、64 hex 名の symlinkや不完全 generationだけを拒否する。`orchestrator/campaign/s8b_attempt_registry.py:509-562,984-1048`, `brief-v2.md:61-62,100-113`

- [推測] core は filesystem を知らないまま、`load_attempt_registry_with_budget_counts(..., initial_started_budget_counts=...) -> (rows, counts)` を追加する。既存 `load_attempt_registry()` の戻り型は変えず、`assert_registry_rows()` の local accumulator を共通 replay helperへ抽出する。`orchestrator/campaign/attempt_registry_core.py:986-1020,1120-1129,1363-1399`

- [推測] 各 generation は最初の canonical genesis 行から schema、cap、recovery policy digest を読み、`s8b_scheduler_accounting.AUTHORITY_ID/AUTHORITY_POLICY_SHA256` を渡してその世代専用 profile を構築し、full replayで digestを再確認する。単一 current profileを旧世代へ流用しない。`orchestrator/campaign/attempt_registry_core.py:654-725`, `orchestrator/campaign/s8b_scheduler_accounting.py:40-48,65-102`

- [推測] `_atomic_update()` は共有 root lock 下で、他世代を protocol SHA 順に replayして countsを累積し、current old bytesとcandidate bytesを同じ initial countsで別々に replayする。candidateだけが上限を越える場合、staging前に拒否する。`orchestrator/campaign/s8b_attempt_registry.py:984-1048`

- [推測] v2 slotを次の 5 軸へ変更する。legacy statistical retry と registry recovery を分離するためである。`orchestrator/campaign/s8b_attempt_profile.py:27-40,53-148`

  ```text
  slot_id =
    (freeze_holdout_key, configuration_id, repetition,
     measurement_ordinal, attempt_ordinal)

  series_key =
    (freeze_holdout_key, configuration_id, repetition,
     measurement_ordinal)

  budget_key =
    (freeze_holdout_key, configuration_id)
  ```

- [推測] planned は `measurement_ordinal=0, attempt_ordinal=0`、legacy retry は campaign の cell-wide `retry_ordinal` を `measurement_ordinal` へ写し、`attempt_ordinal=0` とする。verified recoveryだけが後者を増やすが、その発行側は scope 外かつ pin は空なので本 waveでは ordinal 1 を作らない。全 round × `measurement_ordinal=0..retry_slots_per_cell` を genesisへ事前登録し、実際の start 合計は freeze-wide cap 10で抑える。`orchestrator/campaign/s8b_floor_campaign.py:5886-5907,6169-6187`, `orchestrator/campaign/s8b_holdout_admission.py:1427-1435`

- [推測] 台帳専用理由語彙を次の 4 値に固定し、protocol の既存 4 語をそのまま再利用しない。`orchestrator/campaign/s8b_attempt_profile.py:388-399`, `orchestrator/campaign/s8b_floor_contract.py:96-101`

  ```text
  sealed-probe-competition
  sealed-measurement-launch-failure
  sealed-measurement-output-incomplete
  sealed-measurement-dispersion
  ```

- [推測] `derive_s8b_terminal_projection(sealed_session_record)` を profile 層に置き、sessionの `valid`、`excluded_reason`、`rep_observations`、`session_median` から status、reason、report digest、observation digest、primary valueを機械的に返す。呼び手から reason/statusを受け取らない。`S8B_RETRYABLE_FAILURE_REASONS` はこの戻り値の closed set としてのみ非空になる。`orchestrator/campaign/s8b_attempt_profile.py:388-466`, `orchestrator/campaign/s8b_floor_campaign.py:6128-6165`

- [推測] v2 terminal row に exact `sealed_session_record` objectを追加し、canonical bytes digestが `raw_output_sha256` と一致し、導出 projectionが terminal fieldsと一致することを full replay時にも再検査する。これにより crash後にjournal bytesを再構成できる。`orchestrator/campaign/s8b_attempt_profile.py:291-365`, `orchestrator/campaign/attempt_registry_core.py:1215-1290,1814-1897`

- [推測] classification claim addressとpayloadは full binding 3値と v2 slot 5軸を含める。schemaを v3へ上げ、同じ freeze/slotでも protocolまたはscheduleが違えば別 create-only pathになる。`orchestrator/campaign/s8b_attempt_registry.py:811-901`

### 単位 B: admission 層

- [推測] `CellHoldoutAdmission` に read-only `measurement_generation_claim_digest: str` を追加し、fresh/resume/inspector再構築の全 constructorで `_CellState` と同じ値を射影する。digestの導出式は変更しない。`orchestrator/campaign/s8b_holdout_admission.py:250-259,805-815,1793-1819,6227-6253`

- [推測] current marker用に admission-owned `validate_floor_attempt_consumption_marker(admission, attempt_id)` を追加し、claim、main ledger、marker path、exact schema、全 identityを再導出した opaque capabilityを返す。adapterの `_assert_consumed_marker()` はraw pathを独自導出せず、この検証済み capabilityだけを受ける。legacy v1 marker validatorは既存 cut-6 test用に残す。`orchestrator/campaign/s8b_holdout_admission.py:4435-4489,4519-4824`, `orchestrator/campaign/s8b_attempt_registry.py:1458-1509`

- [推測] read-only inspectorを producer capture と verifier inspection の 2 入口にする。どちらも `_locked_readonly(root)` 内で current protocol generationの全 bytesを読み、世代 genesisからprofileを構築して全行 replayする。`orchestrator/campaign/s8b_holdout_admission.py:589-638,4960-4990`

- [推測] producer captureは full replay後の `N=len(rows)` と `rows[N-1]["event_sha256"]` を返す前に、result予定の全 attemptを検査する。各 attemptは v2 slotへ一意に写り、start、classification、terminal、sealed session recordが一件ずつ必要である。`orchestrator/campaign/s8b_floor_contract.py:182-254`, `orchestrator/campaign/s8b_floor_campaign.py:6373-6382,6577-6589`

- [推測] verifier inspectionはlive全行をreplayした後だけ、`len(rows) >= N` と `rows[N-1]["event_sha256"] == reported head` を比較する。N以後もparse/replay対象なので壊れたtailは拒否し、正当appendは許す。`orchestrator/campaign/attempt_registry_core.py:1363-1399`, `brief-v2.md:46-48`

- [推測] coverageは result側 attempt identity集合と、prefix内で同じ `{campaign_run_id, manifest_sha256, run_relpath}` を持つ sealed terminal集合を双方から比較し、完全一致を要求する。比較の向きは片方向の包含ではなく集合等値である。別campaignやgenesis-onlyはここで拒否する。`orchestrator/campaign/s8b_floor_campaign.py:6577-6589`, `brief-v2.md:39-42,146-148`

### 単位 C: 配線層

- [推測] launcherに `CLASSIFICATION_AUTHORITY_ID`、`classification_authority_policy_document()`、`CLASSIFICATION_AUTHORITY_POLICY_BYTES`、`CLASSIFICATION_AUTHORITY_POLICY_SHA256`、production `ClassificationAuthority` を新設する。policy bytesは fixed pre/post probe、launch-failure precedence、sealed-record reason mappingを列挙し、canonical bytesからdigestを導出する。public launcherからcaller指定 authorityを除く。`orchestrator/campaign/s8b_floor_attempt_launcher.py:25-32,105-110,548-670`, `orchestrator/campaign/s8b_scheduler_accounting.py:65-102`

- [推測] public launcherがpre-probeとpost-probeの両方を所有する。pre-probe競合時は registry genesis確認 → reserve → launcher-owned probe → classify → sealed failure terminalの順で処理し、`capture_measure_point` とadmission ticket消費は呼ばない。campaignからprobe結果を渡す入口は作らない。`orchestrator/campaign/s8b_floor_attempt_launcher.py:238-318,548-645`, `orchestrator/campaign/s8b_floor_campaign.py:6023-6036`

- [推測] 計測経路では launcherが `consume_attempt_ticket` 直後に `capture_measure_point` を呼び、その後current marker capabilityをadmission validatorから得てadapterへ渡す。production defaultはcalibratorのcapture primitiveを使い、nondefault test/pilot seamは明示的なnoncertifying dependencyとして分離する。`orchestrator/calibrator/runner.py:803-905`, `orchestrator/campaign/s8b_floor_campaign.py:5723-5777,7613-7641`

- [推測] `_Runner._run_session()` は session-start recordのexact writer bytesを一度生成し、fsync後にその SHA-256 を reservationへ渡す。resumeでは既存session-startを同じserializerで再構成し、digestを再導出する。`orchestrator/campaign/s8b_floor_campaign.py:1583-1594,5995-6007`

- [推測] `_run_session()` の `self.measure_fn(...)` とpre-probe早期returnをまとめて `launch_floor_attempt(...)` へ置換する。campaignの責務は immutable reservation、closed genesis、measurement coordinates、terminal record builderの構築と、launcher返却recordのjournal appendだけにする。`orchestrator/campaign/s8b_floor_campaign.py:5995-6122`

- [推測] `FloorAttemptTerminal` の各 field は次から導出し、launcherでsealed recordと再照合する。`orchestrator/campaign/s8b_floor_attempt_launcher.py:125-149`, `orchestrator/campaign/s8b_floor_campaign.py:6128-6165`

  | field | 出所 |
  |---|---|
  | [推測] `raw_output_bytes` | journalに書くexact canonical session line |
  | [推測] `terminal_status` | `valid=True`なら`observed`、closed exclusionなら`retryable-failure` |
  | [推測] `report_sha256` | exact session lineのSHA-256 |
  | [推測] `observation_sha256` | valid sessionのcanonical `rep_observations` digest。invalidはnull |
  | [推測] `primary_value` | valid時のsealed `session_median`。invalidはnull |
  | [推測] `finished_at` | session recordへ新設する`finished_iso` |
  | [推測] `campaign_record` | `raw_output_bytes`を再parseしたexact mapping |

- [推測] 二相順序は registry terminal fsync → campaign session fsync とする。v2 terminalのsealed recordを使い、resume開始時にlauncher経由で同じcampaignのterminalを列挙する。registry terminalあり/journal sessionなしならexact recordを一度だけappendし、双方ありならbytes一致、journalだけならfail-closedとする。campaignはadapterを直接importしない。`orchestrator/campaign/s8b_floor_attempt_launcher.py:637-645`, `orchestrator/campaign/s8b_floor_campaign.py:5870-5875,6190-6217`, `orchestrator/tests/test_s8b_attempt_registry.py:1553-1600`

- [推測] registry terminal前のcrashは成果物を発行せずfail-closedとする。自動再測定を新設すると verified recovery 後半へ踏み込むため、本waveのreconciliation対象はterminal-first cutに限定する。`orchestrator/campaign/s8b_attempt_registry.py:1765-2071`, `brief-v2.md:17-18,34-35`

### 単位 D: 契約・consumer 層

- [推測] contractを `LEGACY_RESULT_SCHEMA=v4`、`RESULT_SCHEMA=v5`、`READABLE_RESULT_SCHEMAS={v4,v5}`、schema別 exact key集合へ分ける。`result_keys_for_mode(mode, *, schema, perf_preflight)` はschemaを必須にする。`orchestrator/campaign/s8b_floor_contract.py:29-38,81-87,157-166`

- [推測] v5の `attempt_registry` はexact 7 field objectとする。`chain_head_sha256` は `rows[N-1].event_sha256` の意味に限定する。`orchestrator/campaign/attempt_registry_core.py:233-259`

  ```json
  {
    "schema": "s8b-floor-attempt-registry-proof/v1",
    "registry_schema": "s8b-floor-attempt-registry/v2",
    "freeze_sha256": "<64 lowercase hex>",
    "protocol_sha256": "<64 lowercase hex>",
    "schedule_sha256": "<64 lowercase hex>",
    "row_count": 1,
    "chain_head_sha256": "<64 lowercase hex>"
  }
  ```

- [推測] pure verifierはv4ならproof fieldを禁止して既存受理を維持し、v5ならproof shape、binding、正のN、nonzero headを検査する。live wrapperから渡された独立proofと `reported == independently_replayed_live_prefix` の向きで比較する。`orchestrator/campaign/s8b_floor_stats.py:682-768`

- [推測] live wrapperはv4でregistryを一切読まず、v5だけread-only prefix inspectorを呼ぶ。これによりv4の受理面を増減させない。`orchestrator/campaign/s8b_floor_stats.py:1036-1082`

- [推測] producerはholdout inspection後、proof captureとcoverageが成功してから `assemble_result(..., attempt_registry=proof)` を呼ぶ。`attempts` projectionにはv5から `attempt_id` を追加する。pending bytesはlive self-check後だけ作る。`orchestrator/campaign/s8b_floor_campaign.py:6577-6589,7568-7611,7713-7789`

- [推測] `M-finalize-pending` は既存 `.result.json.pending` のproofを読み直してlive prefix検査し、現在tailから新しいNを採り直さない。そうしないと正当appendだけでpending bytesが変わる。`orchestrator/campaign/s8b_floor_campaign.py:6768-6829,7568-7610`

- [推測] 新規candidate入口はv5-onlyで、v4 downgradeを拒否する。`orchestrator/campaign/s8b_holdout_freeze.py:1417-1442,1619-1643`

- [推測] ratified reverifyはv4/v5をschema別 exact keysで読む。v4は従来どおりregistry非遡及、v5だけlive wrapperを通す。`orchestrator/campaign/s8b_ratified_freeze.py:2333-2390,3253-3302`

- [推測] `_official_earlier_floor_results()` はresult bytesをstrict parseし、v4は既存admission eligibilityだけ、v5はprefix proofとcoverageを検査してからeligibilityを返す。invalid earlier v5は「eligible=false」へ丸めず underivable として拒否する。`orchestrator/campaign/s8b_holdout_freeze.py:1813-1925`

## 却下した代案

- [実測] 現tail完全一致と `len(rows)==N` は正当appendで既発行resultを無効化するため却下する。`brief-v2.md:23-26,46-48`

- [実測] 先頭N行だけをparseする案はN以後の破損を見逃すため却下する。`orchestrator/campaign/attempt_registry_core.py:1363-1399`, `brief-v2.md:46-48`

- [実測] freeze-wide専用budget ledgerまたはgeneration indexはD1340に反するため追加しない。`brief-v2.md:23-24`

- [実測] campaignがpre-probe結果やreasonをlauncherへ渡す案は分類権限をcallerへ戻すため却下する。`brief-v2.md:43-45`

- [実測] legacy retry ordinalを既存`attempt_ordinal`へ直写しする案はcell-wide軸とrepetition内seriesを混同するため却下する。`orchestrator/campaign/s8b_attempt_profile.py:121-143`, `orchestrator/campaign/s8b_floor_campaign.py:5886-5907`

- [実測] v5 proofをoptionalにする案はproducerとconsumer双方からfieldを落とす変異を恒真化するため却下する。`orchestrator/campaign/s8b_floor_contract.py:81-87`

- [実測] admissionの `_FLOOR_RECOVERY_AUTHORITIES` を埋める案はD880に反するため却下する。profile replay用authorityとrecovery発火pinは別物として扱う。`orchestrator/campaign/s8b_holdout_admission.py:93-109`

- [実測] `trial_registry.py` と最終8c発行層のlive再確認はscope外である。`brief-v2.md:17-18,27`

## 赤になる既存 test

### 直接赤

| test | file:line | 理由 |
|---|---:|---|
| [推測] `test_s8b_profile_closes_slot_binding_budget_and_reason_policy` | `test_attempt_registry_core_s8b_profile.py:296-357` | root path、slot identity、空retryable集合、schema v1 pinが変わる |
| [推測] `test_genesis_is_create_only_and_rejects_alternate_or_symlinked_paths` | `test_s8b_attempt_registry.py:1012-1061` | path formatterとpublic `registry_path()` にprotocol引数が必要 |
| [推測] `test_new_registry_directories_fsync_each_parent_entry` | `test_s8b_attempt_registry.py:1296-1329` | protocol directoryが1段増える |
| [推測] marker検査4族 | `test_s8b_attempt_registry.py:897-1009` | raw legacy marker検査からadmission-issued current capabilityへ変わる |
| [推測] launcher 7 node | `test_s8b_floor_attempt_launcher.py:268-678` | pre-probe、production authority、slot 5軸、terminal derivation、public signatureが変わる |
| [推測] `test_floor_campaign_directly_reexports_shared_leaf_objects` | `test_s8b_floor_contract.py:164-184` | `RESULT_SCHEMA == v4` pinがv5へ変わる |
| [推測] `test_result_v4_key_contract_is_mode_conditional_and_exact` | `test_s8b_floor_contract.py:366-383` | schema別v4/v5 key APIへ変わる |
| [推測] `test_pure_verifier_rejects_legacy_result_schema` | `test_s8b_floor_stats.py:1321-1325` | v3拒否の意味は維持するが、期待messageが「v4でない」から「readable schema外」へ変わる。v4正例への転用はしない |
| [推測] direct `assemble_result()` 12 call | `test_s8b_floor_campaign.py:6040-6125,12838-12918` ほか | v5 proofがrequiredになり、従来引数だけではassembly前に止まる |
| [推測] finalize/resume crash nodes | `test_s8b_floor_campaign.py:8451,8702,8976,9174` | registry-first reconciliationとpending proof固定が新しい状態機械になる |

### fixture経由でtransitiveに赤

| fixture / family | file:line | 波及 |
|---|---:|---|
| [推測] `_run_campaign()` | `test_s8b_floor_campaign.py:751-788` | file内144 call siteへlauncher配線、authority、marker、v5 proofが波及する |
| [推測] `candidate_repository()` | `s8b_v2_freeze_fixture.py:337-445` | current定数がv5になるがattempt registryとproofを作らない。holdout freeze側34 callへ波及する |
| [推測] `_build_independent_launch_repo()` | `test_s8b_ratified_verify.py:430-535` | current v5 resultにproof/live registryがない。約10 callへ波及する |
| [推測] `build_production_emitter_g1()` / `append_production_emitter_g2()` | `test_s8b_ratified_freeze.py:966-1203` | emitter後のadmission root再構築がattempt registryを再構築しない。約18 callへ波及する |
| [推測] `build_floor_admission_evidence()` | `s8b_floor_evidence_fixture.py:192-351` | pre-probe competingをmarker無しにする既存挙動は維持できるが、v5 registry lifecycle/proof fixtureが不足する |

## テスト計画

### 正例

- [推測] `test_s8b_attempt_registry.py::test_two_protocol_generations_use_distinct_registry_and_claim_paths` — 同じfreeze/slotを2世代でreserveからterminalまで完走する。`s8b_attempt_registry.py:451-491,811-901`

- [推測] `test_s8b_attempt_registry.py::test_cross_generation_budget_accepts_exact_freeze_limit` — 世代別profileをgenesisから解決し、合計10件ちょうどを受理する。`attempt_registry_core.py:986-1129`

- [推測] `test_attempt_registry_core_s8b_profile.py::test_measurement_ordinal_is_separate_from_recovery_ordinal` — legacy retryとrecovery seriesを別軸として固定する。`s8b_attempt_profile.py:121-143`

- [推測] `test_s8b_floor_attempt_launcher.py::test_pre_probe_competition_reserves_and_terminalizes_without_capture` — capture未呼出しのままstart/classification/terminalが残る。`s8b_floor_attempt_launcher.py:548-645`

- [推測] `test_s8b_floor_campaign.py::test_registry_terminal_is_reconciled_to_missing_session_on_resume` — registry-first cut後にexact sealed recordをjournalへ一度だけ復元する。`s8b_floor_campaign.py:5870-5875,6190-6217`

- [推測] `test_s8b_holdout_admission.py::test_v5_prefix_proof_survives_valid_later_append` — N以後の正当appendを受理する。`s8b_holdout_admission.py:612-638`

- [推測] `test_s8b_floor_stats.py::test_pure_verifier_accepts_v4_without_registry_proof` — v4非遡及を固定する。`s8b_floor_stats.py:682-768`

- [推測] `test_s8b_ratified_verify.py::test_historical_reverify_accepts_v4_without_registry_access` — inspectorを呼ぶと失敗するstubでv4 skipを証明する。`s8b_ratified_freeze.py:3253-3302`

- [推測] `test_s8b_holdout_freeze.py::test_earlier_valid_v5_is_checked_before_selection` — earlier v5のproofとcoverageが正常なら従来のearliest判定へ進む。`s8b_holdout_freeze.py:1813-1925`

### 束縛の負例

| 向き | node案 | 恒真化を避ける理由 |
|---|---|---|
| [推測] artifact proof欠落 | `test_s8b_floor_stats.py::test_v5_rejects_missing_attempt_registry_proof` | validなexpected proofを別入力で保持し、top-level fieldだけを除く |
| [推測] reported head改竄 | `test_s8b_floor_stats.py::test_v5_rejects_reported_prefix_head_tamper` | proof shape/binding/Nは正常にし、expected headとの比較だけを発火させる |
| [推測] live registry不在 | `test_s8b_ratified_verify.py::test_v5_reverify_rejects_missing_live_registry` | artifactとjournalを固定し、live fileだけを除く |
| [推測] genesis-only | `test_s8b_holdout_admission.py::test_v5_coverage_rejects_genesis_only_registry` | `{N=1,head}` 自体は正しくし、coverageだけを不足させる |
| [推測] 別campaign | `test_s8b_holdout_admission.py::test_v5_coverage_rejects_other_campaign_registry` | binding/head/lifecycleは全てvalidにし、sealed campaign identityだけを変える |
| [推測] terminal欠落 | `test_s8b_holdout_admission.py::test_v5_coverage_rejects_start_without_terminal` | result attemptとstartは一致させ、terminal対応だけを欠かす |
| [推測] pre-probe attempt欠落 | `test_s8b_floor_campaign.py::test_v5_rejects_pre_probe_exclusion_missing_from_registry` | journal/resultにはpre-probe sessionを残し、そのregistry lifecycleだけを除く |
| [推測] v4 downgrade | `test_s8b_holdout_freeze.py::test_new_candidate_rejects_valid_v4_result` | historical v4正例を別nodeで緑に保ち、新規candidate境界だけを見る |
| [推測] invalid earlier v5 | `test_s8b_holdout_freeze.py::test_later_v5_rejects_invalid_earlier_v5_proof` | later resultを正常にし、earlier proofだけを壊す |

### 台帳部品検査の負例

| 部品 | node案 | 恒真化を避ける理由 |
|---|---|---|
| [推測] N行内chain改竄 | `test_prefix_inspector_rejects_tamper_inside_proved_prefix` | reported proofを固定し、live rowだけを再chainせず変更する |
| [推測] N行以後の破損 | `test_prefix_inspector_rejects_malformed_row_after_n` | 先頭N行とreported headを一致させ、full replayだけが破損を検出する |
| [推測] N行以後のchain切断 | `test_prefix_inspector_rejects_broken_chain_after_n` | JSON shapeはvalidにしてtail chain検査だけを発火させる |
| [推測] generation sibling file | `test_generation_enumerator_ignores_freeze_sibling_file` | valid generationとcatalog風siblingを同居させ、ignore規則を固定する |
| [推測] 64hex symlink generation | `test_generation_enumerator_rejects_hex_symlink` | sibling file ignoreとは分離し、directory authorityだけを検査する |
| [推測] 世代予算reset | `test_second_protocol_cannot_reset_freeze_budget` |第2世代local countは0かつvalidにし、横断accumulatorだけを発火させる |
| [推測] genesis profile差替え | `test_generation_replay_uses_each_genesis_profile` | 旧世代をそのgenesis profileでのみ通る形にし、current profile流用を検出する |
| [推測] sealed reason改竄 | `test_registry_replay_rejects_terminal_reason_not_derived_from_session` | chainを正しく再計算し、sealed recordとterminal projectionの差だけを残す |

## 変異事前登録の候補

| ID | 変異位置 | 変異内容 | KILLする test node id | 単一理由性の確認 |
|---|---|---|---|---|
| [推測] M1 | `s8b_attempt_profile.py:378-386` | pathから`{protocol_sha256}`を除く | `orchestrator/tests/test_s8b_attempt_registry.py::test_two_protocol_generations_use_distinct_registry_and_claim_paths` | 両genesisは単独ではcore-validで、赤理由はpath衝突だけ |
| [推測] M2 | `s8b_attempt_registry.py:984-1017` 周辺 | other-generation countsをcurrent candidateへ渡さない | `...::test_second_protocol_cannot_reset_freeze_budget` | 第2世代local gateは通るため、横断gate以外に拒否層がない |
| [推測] M3 | `s8b_attempt_registry.py:811-839` | claim addressからprotocol/scheduleを除く | `...::test_two_protocol_generations_use_distinct_registry_and_claim_paths` | registry pathは別々でvalidなため、claim create-only衝突だけが赤理由 |
| [推測] M4 | `s8b_floor_attempt_launcher.py:548-645` の新pre-probe branch | 競合時のregistry terminal callを削除してrecordだけ返す | `orchestrator/tests/test_s8b_floor_attempt_launcher.py::test_pre_probe_competition_reserves_and_terminalizes_without_capture` | recorder fakeのcomponent testでproof層を呼ばず、terminal event欠落だけを検査する |
| [推測] M5 | `s8b_holdout_admission.py:4969-4990` 隣のcoverage helper | result attemptとterminal集合の等値比較を削除 | `...::test_v5_coverage_rejects_genesis_only_registry` | N/head/binding/genesisは全てvalidで、他gateは同じ入力を拒否しない |
| [推測] M6 | 同prefix inspector | full replayを先頭N行だけのreplayへ縮小 | `...::test_prefix_inspector_rejects_malformed_row_after_n` | prefix/headはvalidで、tail破損を拒否する層はこのfull replayだけ |
| [推測] M7 | `s8b_floor_stats.py:734-768` の新proof比較 | reported/live proof等値比較を削除 | `orchestrator/tests/test_s8b_floor_stats.py::test_v5_rejects_reported_prefix_head_tamper` | pure verifier直接testとし、live wrapperやcoverageへ到達させない |
| [推測] M8 | `s8b_holdout_freeze.py:1424-1440` | candidateのv5-onlyをreadable v4/v5へ緩和 | `...::test_new_candidate_rejects_valid_v4_result` | fixture v4はhistorical verifierでvalid、拒否点はcandidate境界だけ |
| [推測] M9 | `s8b_holdout_freeze.py:1865-1925` | earlier v5のprefix inspectionをskip | `...::test_later_v5_rejects_invalid_earlier_v5_proof` | helper直接testでselection後段を呼ばず、earlier inspectionだけを測る |

- [実測] 前回M8の `row_count > 0` 変異は後段proof mismatchと重複するので登録しない。positive-row validatorを単独で変異するなら、live expected proofを渡さないcomponent validator testへ再照準する。`orchestrator/campaign/s8b_floor_stats.py:682-768`

- [実測] producer field削除、binding比較削除、event hash再計算削除は複数のexact-key/path/core gateと重なるため登録しない。`orchestrator/campaign/attempt_registry_core.py:442-465,654-738`, `orchestrator/campaign/s8b_attempt_registry.py:451-506`

## 実装単位の分割

- [推測] brief-v2のA/B/C/Dを採る。編集pathは次のとおり相互に重複させない。`brief-v2.md:133-142`

1. [推測] 単位A

   - `orchestrator/campaign/attempt_registry_core.py`
   - `orchestrator/campaign/s8b_attempt_profile.py`
   - `orchestrator/campaign/s8b_attempt_registry.py`
   - `orchestrator/tests/test_attempt_registry_core_s8b_profile.py`
   - `orchestrator/tests/test_s8b_attempt_registry.py`

2. [推測] 単位B

   - `orchestrator/campaign/s8b_holdout_admission.py`
   - `orchestrator/tests/s8b_floor_evidence_fixture.py`
   - `orchestrator/tests/test_s8b_holdout_admission.py`

3. [推測] 単位C

   - `orchestrator/campaign/s8b_floor_attempt_launcher.py`
   - `orchestrator/campaign/s8b_floor_campaign.py`
   - `orchestrator/tests/test_s8b_floor_attempt_launcher.py`
   - `orchestrator/tests/test_s8b_floor_campaign.py`

4. [推測] 単位D

   - `orchestrator/campaign/s8b_floor_contract.py`
   - `orchestrator/campaign/s8b_floor_stats.py`
   - `orchestrator/campaign/s8b_holdout_freeze.py`
   - `orchestrator/campaign/s8b_ratified_freeze.py`
   - `orchestrator/tests/test_s8b_floor_contract.py`
   - `orchestrator/tests/test_s8b_floor_stats.py`
   - `orchestrator/tests/test_s8b_holdout_freeze.py`
   - `orchestrator/tests/test_s8b_ratified_verify.py`
   - `orchestrator/tests/test_s8b_ratified_freeze.py`
   - `orchestrator/tests/s8b_v2_freeze_fixture.py`
   - `orchestrator/tests/acceptance_duration_ledger.json`

- [推測] 依存順は A → B → Dのcontract/proof leaf → Cのwriter/reconciliation → Dの全consumer/fixture とする。Cはv5 schemaとprefix APIを消費し、DはCが発行するsealed lifecycleを検査するため、C/Dの独立greenは要求しない。`orchestrator/campaign/s8b_floor_campaign.py:6485-6650,7568-7609,7735-7789`, `orchestrator/campaign/s8b_floor_contract.py:81-87,157-166`

- [推測] checkpointは、(1) A/Bのauthority・ordinal・marker API、(2) C/D統合後の全fixture更新、(3) 事前登録変異のkill確認とする。全単位をunlandedで保持し、最終的に一度だけcommit/landする。`brief-v2.md:23,128-142`

## 規模の再評価

| 単位 | changed LOC見積もり | 赤になる既存node概数 | 主因 |
|---|---:|---:|---|
| [推測] A | 600-850 | 35-55 | schema v2、slot codec、世代profile、横断replay、claim世代化 |
| [推測] B | 450-700 | 25-45 | claim projection、marker capability、full prefix replay、coverage |
| [推測] C | 850-1,300 | 145-180 | launcher所有probe、capture配線、terminal projection、二相reconcile、共有campaign helper |
| [推測] D | 750-1,150 | 70-110 | v4/v5 dispatch、5 consumer面、candidate/ratified fixture |
| [推測] 合計 | 2,650-4,000 | unique 170-230 | C/Dとfixture familyの重複を除いた概数 |

- [実測] 現時点でも `_run_campaign` call siteは144、candidate fixture callは34、independent ratified fixtureは約10、production emitter helper群は約18 callある。`orchestrator/tests/test_s8b_floor_campaign.py:751-788`, `orchestrator/tests/s8b_v2_freeze_fixture.py:367-445`, `orchestrator/tests/test_s8b_ratified_verify.py:478-535`, `orchestrator/tests/test_s8b_ratified_freeze.py:966-1203`

- [推測] (P1-i) の「通常の1 waveで4単位を安全に実装し、そのまま1 commitへ統合できる規模」は否定する。1 commitへの格納自体は可能だが、2,650行以上と170 node以上の更新を一回の実装・レビューで扱う規模ではない。`brief-v2.md:153`

- [推測] D1341と両立する現実案は、A/B/C/Dを同じ統合worktree内のuncommitted checkpointとして順に作り、各checkpointを差分レビューした後、統合suiteと変異確認を通した一つの最終commitだけをlandする形である。writer-onlyまたはverifier-only commitは作らない。`brief-v2.md:23,128-142`

## 親 brief への異議

- [実測] **(P1-a) は成立する。** protocol hashはcanonical protocolから導出され、admissionはfixed raw bytesおよびindexed recordと照合し、bindingにも既存fieldとして存在する。`orchestrator/campaign/s8b_floor_campaign.py:470-481,7150-7166`, `orchestrator/campaign/s8b_holdout_admission.py:691-736`, `orchestrator/campaign/s8b_attempt_profile.py:43-49`

- [推測] **(P1-f) は成立する。** ただしcurrent terminal rowにはattempt/campaign identityがないため、v2 terminalへsealed session recordを入れることが必要条件である。これは既存registry rowのschema拡張であり、新しい成果物や専用ledgerではない。`orchestrator/campaign/s8b_attempt_profile.py:333-350`, `orchestrator/campaign/s8b_floor_campaign.py:6128-6165`

- [推測] **(P1-g) は成立する。** pre-probe exclusionは既存statusの `retryable-failure` で表現でき、理由だけを台帳専用closed vocabularyへ変換する。新statusは不要である。`orchestrator/campaign/s8b_attempt_profile.py:388-395`, `orchestrator/campaign/attempt_registry_core.py:933-983`

- [推測] **(P1-h) は成立する。** ただしregistry terminalからjournal recordを復元するには、v2 terminalがsealed record本体を保持しなければならない。現v1 fieldsだけでは成立しないため、このschema変更をCの任意事項にしてはならない。`orchestrator/campaign/attempt_registry_core.py:1814-1897`, `orchestrator/campaign/s8b_floor_attempt_launcher.py:628-645`

- [実測] **(P1-i) は規模主張として成立しない。** current静的fanoutだけで164件超、今回追加されるT-1851前半のschema/reason/reconciliationを含めると2,650-4,000 changed LOC規模になる。`brief-v2.md:12-15,135-153`, `orchestrator/tests/test_s8b_floor_campaign.py:751-788`

- [実測] 親裁定1から6を静的実測で反証する材料はない。親裁定1はgenesis-only、別campaignを実際に塞ぎ、親裁定2は現pre-probe早期returnを閉じ、親裁定3はfull replayとprefix比較を両立させる。`orchestrator/campaign/s8b_floor_campaign.py:6023-6036`, `orchestrator/campaign/attempt_registry_core.py:1363-1399`, `brief-v2.md:37-62`

- [実測] briefの編集path表はproduction 10 file + test/support 13 fileの計23 pathである。段4文書の「production 11 + test/support 13」という件数とは1件ずれるが、追加すべき11番目のproduction pathは現コードからは確認できない。`brief-v2.md:133-140`

## 総括

- [推測] 実装可能である。中核は、registry v2で `measurement_ordinal` と recovery `attempt_ordinal` を分離し、世代ごとのgenesis profileで横断budgetをreplayし、sealed session recordからterminal reasonを再導出することである。`s8b_attempt_profile.py:27-40,388-466`, `attempt_registry_core.py:986-1129`

- [推測] producer側はlauncher-owned pre-probeを含む全attemptをregistry-firstでterminalizeし、journal欠落をsealed terminalからreconcileする。consumer側はv5だけ `{N, head_at_N}` とcampaign coverageを検査し、v4は非遡及のまま維持する。`s8b_floor_campaign.py:5995-6165`, `s8b_floor_stats.py:682-768,1036-1082`

- [実測] pytestは実行しておらず、緑は報告しない。実装はA/B/C/Dをunlanded checkpointとして進め、統合後の一つのcommitだけをlandするのがD1341と規模の両方に適合する。`brief-v2.md:23,128-153`