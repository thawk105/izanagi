## 前提の実測

- [実測] 指定 6 文書を順番どおり読了した。sandbox は read-only であり、pytest は実行していない。以下は指定 worktree 内だけの静的検査結果である。

- [実測] 現在の path は `S8B_REGISTRY_LAYOUT.registry_path = floor-attempt-registries/{freeze_sha256}/registry.jsonl` で、世代次元がない。`orchestrator/campaign/s8b_attempt_profile.py:378-386`

- [実測] repo 内に `floor-attempt-registries/**/registry.jsonl` は 0 件だった。`rg --files -uu` で tracked/untracked を含めて検索した。shared admission root は Git common dir 配下へ解決されるため、指定 worktree 外の実在までは一般化しない。`orchestrator/campaign/s8b_holdout_admission.py:510-527`

- [実測] 同じ freeze `315b1eb8...bc688` を参照する protocol が 2 件あり、raw SHA-256 はそれぞれ `261cec1c...e74aac` と `2c8cf9be...dfa58a` である。`output/s8b-freeze/floor_protocol.json:1`, `output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json:1`

- [実測] campaign の `protocol_sha256` は normalized protocol の canonical JSON SHA-256 で、admission は固定 protocol bytes の SHA-256 と一致させる。したがって世代識別子には既存 `protocol_sha256` を使用できる。新しい世代番号は不要である。`orchestrator/campaign/s8b_floor_campaign.py:470-481,7166`, `orchestrator/campaign/s8b_holdout_admission.py:691-736`

- [実測] `S8BAttemptBinding` は freeze/protocol/schedule の 3 digest を identity にする。現 production の writer 経路ではまだ生成されず、production 内の唯一の構築は recovery verifier 側である。`orchestrator/campaign/s8b_attempt_profile.py:43-49,151-215`, `orchestrator/campaign/s8b_holdout_admission.py:5199-5218`

- [実測] path 導出の production 呼び手は次のとおりである。

  - `_entry_paths()` は定義 1、内部 call site 11 件。`orchestrator/campaign/s8b_attempt_registry.py:462-482,488-490,500-502,1066-1070,1098-1100,1148-1150,1301-1303,1522-1524,1634,1685,1739,1827-1829`
  - public `registry_path()` の production caller は 0、test caller は 2 件。`orchestrator/campaign/s8b_attempt_registry.py:485-491`, `orchestrator/tests/test_s8b_attempt_registry.py:1040,1052`
  - admission の raw reader は `_floor_registry_path()` 1 件。`orchestrator/campaign/s8b_holdout_admission.py:4960-4966,5048`
  - layout template を直接 format する test helper は 4 面。`orchestrator/tests/test_s8b_attempt_registry.py:1020`, `orchestrator/tests/test_s8b_holdout_admission.py:1990`, `orchestrator/tests/test_s8b_floor_campaign.py:11027`, `orchestrator/tests/test_attempt_registry_core_s8b_profile.py:347-350`

- [実測] mutation はすべて shared admission root の単一 `ledger.lock` を排他取得する。per-registry lock は存在しない。read-only verifier 用には同じ inode の shared lock がある。`orchestrator/campaign/s8b_holdout_admission.py:545-638`, `orchestrator/campaign/s8b_attempt_registry.py:984-1048`

- [実測] 現 budget は単一 registry replay 内の `started_budget_counts[(freeze_holdout_key, configuration_id)]` だけで計数される。`orchestrator/campaign/attempt_registry_core.py:986-1020,1120-1129`, `orchestrator/campaign/s8b_attempt_profile.py:405-408,447-456`

- [実測] 実 protocol の `n_sessions=8`、`retry_slots_per_cell=2` で、cell ごとの frozen ticket 数と現 profile cap は `10` に導出できる。`output/s8b-freeze/floor_protocol.json:1`, `orchestrator/campaign/s8b_holdout_admission.py:1427-1435,1802-1815`

- [実測] 現在の production 計測点は `_Runner._run_session()` の `self.measure_fn(...)` である。default closure は最終的に `measure_point()` を直接呼ぶ。`orchestrator/campaign/s8b_floor_campaign.py:5995-6122,7613-7641`

- [実測] S3 は現在の field だけでは到達不能である。

  - recovery authority は `_FLOOR_RECOVERY_AUTHORITIES = frozenset()` で、実値が 0 件。`orchestrator/campaign/s8b_holdout_admission.py:93-109`
  - classification authority は production constant、protocol field、admission fieldのいずれにも存在せず、test literal だけがある。`orchestrator/campaign/s8b_floor_attempt_launcher.py:105-110,648-669`, `orchestrator/tests/test_s8b_floor_attempt_launcher.py:322-323,669-671`
  - `run_start_receipt_sha256` に対応する campaign field はない。session-start は fsync されるが、その bytes digest を返さない。`orchestrator/campaign/s8b_floor_campaign.py:1583-1594,6000-6007`
  - `admission_claim_digest` は `_CellState.measurement_generation_claim_digest` に存在するが、公開 `CellHoldoutAdmission` にはない。`orchestrator/campaign/s8b_holdout_admission.py:250-259,389-403,1802-1815`
  - current consumption marker は `measurement-generation-consumed` の v1 measurement-generation schemaだが、adapter は旧 `consumed` path の `s8b-holdout-attempt-consumption/v1` だけを読む。`orchestrator/campaign/s8b_holdout_admission.py:4435-4489,4519-4546`, `orchestrator/campaign/s8b_attempt_registry.py:55-68,1458-1509`
  - campaign の retry ordinal は cell-wide、registry の `attempt_ordinal` は `(cell, repetition)` 内 prefix である。さらに retryable reason 集合が空なので通常の failed measurement 後に ordinal 1 を開けない。`orchestrator/campaign/s8b_floor_campaign.py:5884-5907,6169-6187`, `orchestrator/campaign/s8b_attempt_profile.py:388-399`, `orchestrator/campaign/attempt_registry_core.py:1081-1119`

- [実測] result は v4 単一定数、単一 key 集合である。consumer の current-schema 等値判定は stats、holdout freeze、ratified freeze の 3 面にある。`orchestrator/campaign/s8b_floor_contract.py:29-38,81-87,157-166`, `orchestrator/campaign/s8b_floor_stats.py:734-748`, `orchestrator/campaign/s8b_holdout_freeze.py:1424-1440`, `orchestrator/campaign/s8b_ratified_freeze.py:2333-2390`

## 推奨プラン

### S1 台帳の世代分割

- [推測] exact path を次へ変更する。

  `floor-attempt-registries/{freeze_sha256}/{protocol_sha256}/registry.jsonl`

  freeze を外側に残すことで S2 の freeze-wide 列挙を index 無しで閉じる。`orchestrator/campaign/s8b_attempt_profile.py:378-386`

- [推測] signature は次へ変更する。

  - `_relative_registry_path(freeze_sha256, protocol_sha256)`。`orchestrator/campaign/s8b_attempt_registry.py:451-459`
  - `_entry_paths(..., freeze_sha256, protocol_sha256, requested_registry_path=None)`。`orchestrator/campaign/s8b_attempt_registry.py:462-482`
  - `registry_path(repo_root, *, freeze_sha256, protocol_sha256)`。`orchestrator/campaign/s8b_attempt_registry.py:485-491`

- [実測] 11 個の `_entry_paths()` call site は全て `binding` または `_AttemptState.binding` を既に持つため、新しい情報源は不要である。`orchestrator/campaign/s8b_attempt_registry.py:488-490,500-502,1066-1070,1098-1100,1148-1150,1301-1303,1522-1524,1634,1685,1739,1827-1829`

- [推測] admission の `_floor_registry_path(state)` は `state.row["freeze_sha256"]` と `state.row["protocol_sha256"]` の両方を template へ渡す。`orchestrator/campaign/s8b_holdout_admission.py:4960-4966`

- [実測] repo 内 artifact は 0 件なので、repo 内 migration は不要である。既存 path の移動、symlink、互換 reader は追加しない。

### S2 予算の横断 replay

- [推測] generic core は filesystem を知らないまま、budget accumulator を返せる pure API だけを追加する。

  ```python
  def load_attempt_registry_with_budget_counts(
      data: bytes,
      *,
      profile: DomainProfile[SlotT, BindingT],
      expected_binding: BindingT | None = None,
      initial_started_budget_counts: Mapping[Hashable, int] | None = None,
  ) -> tuple[RegistryRows, dict[Hashable, int]]:
  ```

  実装位置は `_load_registry_bytes()` / `load_attempt_registry()` 隣で、現 `assert_registry_rows()` の local accumulator を private replay helperへ抽出する。既存 `load_attempt_registry()` の戻り型は変えない。`orchestrator/campaign/attempt_registry_core.py:986-1020,1120-1129,1363-1399`

- [推測] 「同じ freeze の全世代」を列挙する権限は adapter に置く。canonical filesystem path と mutation を所有する層だからである。core や campaign に directory enumeration を持たせない。`orchestrator/campaign/s8b_attempt_registry.py:451-490,984-1048`

- [推測] adapter に次を追加する。

  ```python
  def _freeze_registry_paths_locked(
      root: Path, *, freeze_sha256: str
  ) -> tuple[Path, ...]:
      ...
  ```

  `floor-attempt-registries/{freeze_sha256}` の直下を読み、名前が lowercase 64 hex の real directoryで、その中の `registry.jsonl` が no-follow regular fileであるものを protocol SHA 順に返す。未知 entry、symlink、不完全 generation は fail-closed とする。専用 ledger、index file、pointer は作らない。

- [推測] `_atomic_update()` の `with admission._locked(root)` 内で次の順に行う。`orchestrator/campaign/s8b_attempt_registry.py:1003-1017`

  1. current path 以外を protocol SHA 順に replayし、`other_counts` を得る。
  2. current old bytes を `initial_started_budget_counts=other_counts` で replayする。
  3. transition を作る。
  4. candidate を再び `initial_started_budget_counts=other_counts` で replayする。
  5. global cap を越えなければ初めて staging、replace、fsyncへ進む。

- [実測] lock 規約は「shared root の `ledger.lock` を 1 回だけ排他取得」で閉じる。per-generation lock は追加せず、nested lock も取らない。create、新 generation directory 作成、enumeration、全 replay、candidate replace が同じ lock区間になる。read-only proof は同じ inode の shared lockだけを取る。`orchestrator/campaign/s8b_holdout_admission.py:588-638`

### S3 配線

- [実測] 差し替え seam は `_Runner._run_session()` の `self.measure_fn(...)` と直後の campaign-owned post probeである。ここを launcher の reserve/capture/classify/open/terminal に置換する。`orchestrator/campaign/s8b_floor_campaign.py:6038-6122`, `orchestrator/campaign/s8b_floor_attempt_launcher.py:548-670`

- [推測] campaign は adapter を importせず、`s8b_floor_attempt_launcher` だけを importする。meta-test は exact token `s8b_attempt_registry` を campaign/admission ASTから検出するため、この経路は抵触しない。`orchestrator/tests/test_s8b_attempt_registry.py:1553-1599`

- [実測] launcher input の充足状況は次のとおりである。

| launcher input | campaign/admission source | 判定 |
|---|---|---|
| [実測] `FloorAttemptReservation.repo_root` | `holdout_repo_root`。`s8b_floor_campaign.py:7095-7098,7657-7666` | 充足 |
| [実測] `profile.max_consumptions_per_budget_key` | `protocol["n_sessions"] + protocol["retry_slots_per_cell"] = 10`。`:5860-5863`, `s8b_holdout_admission.py:1427-1435` | 充足 |
| [実測] recovery authority 2 field | production set が空。`s8b_holdout_admission.py:93-109` | 不足 field |
| [実測] `binding.freeze_sha256` | `self.freeze_sha256`。`s8b_floor_campaign.py:5843-5845` | 充足 |
| [実測] `binding.protocol_sha256` | `self.protocol_sha256`。同上 | 充足 |
| [実測] `binding.schedule_sha256` | `canonical_json_bytes(self.schedule)` の hash。現 recovery helperと同じ導出。`test_s8b_floor_campaign.py:10950-10955` | 充足 |
| [実測] planned `slot_id` | `cell.holdout_id`, `cell.configuration_id`, `round-1`, `0`。`s8b_floor_campaign.py:5995-6007` | 充足 |
| [実測] retry `slot_id` | campaign は cell-wide retry、registry は repetition内 prefix。`s8b_floor_campaign.py:6169-6187`, `attempt_registry_core.py:1081-1119` | 不足軸 |
| [実測] `run_start_receipt_sha256` | session-start bytes は永続化されるが digest field/戻り値がない。`s8b_floor_campaign.py:1583-1594,6000-6007` | 不足 field |
| [実測] `process_identity` | campaign-start/resume-start rowsにある。ただし campaign は `starttime=None` を許す一方、core は拒否する。`:6291-6318`, `attempt_registry_core.py:293-312` | 条件付き |
| [実測] `started_at` | session-start の `started_iso`。`s8b_floor_campaign.py:6002-6007` | 充足 |
| [実測] `admission_claim_digest` | private `_CellState.measurement_generation_claim_digest` にだけある。`s8b_holdout_admission.py:389-403,1802-1815` | 不足公開 field |
| [実測] attempt/run/manifest/path/cell identity | `_run_session` localsと `_Runner` fields。`s8b_floor_campaign.py:5995-6010,5843-5845` | 充足 |
| [実測] `FloorAttemptRegistryGenesis.slots` | planned は導出可能、retry cross-product は現 ordinal意味では不正。`attempt_registry_core.py:483-509` | 不足軸 |
| [実測] `FloorMeasurementCapture` の座標 | binary/cell records/threads、contract clocks、protocol extime/reps/workload/numactl/use_perf、consumed observation token。`:6009-6016,7616-7641` | 充足 |
| [実測] `FloorPostProbeCapability` | launcher factory `floor_post_probe_capability()`。`s8b_floor_attempt_launcher.py:269-295` | 充足 |
| [実測] `ClassificationAuthority` | production source 0 件。`s8b_floor_attempt_launcher.py:105-110,648-669` | 不足 field |
| [推測] `terminal_builder` | `_project_scalepoint()` と `_finish_session()` を「record構築」と「journal emit」に分離し、前者から `FloorAttemptTerminal` を作れる。`s8b_floor_campaign.py:1881-1959,6128-6165` | 実装可能 |

- [推測] launcher 内部で private `rep_observations` list を作って `capture_measure_point()` へ渡す。campaign からこの sink を渡すのは現 allowlist が意図的に拒否しているため行わない。`orchestrator/calibrator/runner.py:803-824,933-1054`, `orchestrator/campaign/s8b_floor_attempt_launcher.py:408-440`

- [実測] current marker schema/path と adapter期待値の不一致も同じ変更単位で直す必要がある。current measurement-generation markerを admission所有の exact validatorで再導出し、adapterがその検証済み markerだけを observation開始時に受ける形にする。legacy markerの既存 test面は維持する。`orchestrator/campaign/s8b_holdout_admission.py:4443-4546,4675-4820`, `orchestrator/campaign/s8b_attempt_registry.py:1458-1509`

- [実測] recovery authority、classification authority、run-start receipt、retry ordinal軸を推測値で埋めることはできない。したがって現 briefのままS3を実装開始してはならない。これらを同じ D1341 land単位へ明示的に追加する再briefが必要である。

### S4 束縛

- [推測] `s8b_floor_contract.py:29-38,81-87,157-166` を次の構成にする。

  - `LEGACY_RESULT_SCHEMA = "s8b-floor-result/v4"`
  - `RESULT_SCHEMA = "s8b-floor-result/v5"`
  - `READABLE_RESULT_SCHEMAS = {v4, v5}`
  - `_RESULT_KEYS_V4 =` 現集合
  - `_RESULT_KEYS_V5 = _RESULT_KEYS_V4 | {"attempt_registry"}`
  - `result_keys_for_mode(mode, *, schema=RESULT_SCHEMA, perf_preflight=None)`

- [推測] v5 の `attempt_registry` は exact 7 field objectとする。

  ```json
  {
    "schema": "s8b-floor-attempt-registry-proof/v1",
    "registry_schema": "s8b-floor-attempt-registry/v1",
    "freeze_sha256": "...",
    "protocol_sha256": "...",
    "schedule_sha256": "...",
    "row_count": 1,
    "chain_head_sha256": "..."
  }
  ```

  `row_count` は正整数、digest は lowercase SHA-256、binding 3 値は expected protocol/freeze/scheduleから独立比較する。`orchestrator/campaign/s8b_attempt_profile.py:151-215`, `orchestrator/campaign/attempt_registry_core.py:233-259`

- [推測] admission に read-only inspector を 2 入口追加する。`orchestrator/campaign/s8b_holdout_admission.py:4960-4990,5687-5802`

  - producer用 capture: full valid registryを replayし、現 `N=len(rows)` と `rows[N-1].event_sha256` を返す。
  - verifier用 prefix: artifact の正の `N` を受け、live fileの先頭 N 行だけを canonical parse、chain replayし、N 行目の headを返す。N より後の正当な appendは比較対象にしない。

- [推測]比較方向は常に `reported_proof == independently_replayed_live_prefix_proof` とする。現 tailとの比較、`len(live_rows) == N`、full file hash比較は置かない。D1337の prefix証明を直接実装する。

- [推測] producer は normal completion と finalize-pending の両方で proof capture後に `assemble_result(..., attempt_registry=proof)` を呼ぶ。v5 fieldを result/json/mdへ記録し、live self-check完了前には pending bytesも作らない。`orchestrator/campaign/s8b_floor_campaign.py:6485-6635,7568-7609,7713-7759`

- [推測] `verify_floor_artifact()` は pureのまま keyword-only `expected_attempt_registry=None` を追加する。v5はexact shapeとreported/live完全一致、v4はproof fieldを禁止し要求もしない。`orchestrator/campaign/s8b_floor_stats.py:682-768`

- [推測] `verify_floor_artifact_with_live_admission()` は artifact schemaがv5の場合だけreported `row_count` を使ってprefix inspectorを呼ぶ。v4ではregistryを一切読まない。`orchestrator/campaign/s8b_floor_stats.py:1036-1082`

- [推測] 新規 candidate入口はv5-onlyを維持する。historical/ratified readerはv4/v5をschema別exact keysで読む。`orchestrator/campaign/s8b_holdout_freeze.py:1424-1440,1620-1630`, `orchestrator/campaign/s8b_ratified_freeze.py:2333-2390,3253-3302`

- [推測] `s8b_attempt_registry.py:2-16` の docstringは「adapter/mutationの唯一所有者」に限定し、read-only registry verifierはholdout admissionが所有すると明記する。

- [実測] 前 wave must-fixの pure verifier v5正例として、既存の次 2 nodeをv5 proof込みへ更新する。`orchestrator/tests/test_s8b_floor_campaign.py:9231,12918`

  - `test_end_to_end_golden_floor_values_and_tamper_detection`
  - `test_verify_floor_artifact_binaries_positive_and_negative`

## 却下した代案

- [実測] tail完全一致は、後続の正当なappendで既発行v5を無効にするため却下する。

- [実測] freeze-wide budget ledgerまたはindex fileはD1340に反するため却下する。

- [実測] protocol世代番号の新設は、既存のauthenticated `protocol_sha256` で十分なので却下する。`s8b_floor_campaign.py:7166`, `s8b_holdout_admission.py:691-736`

- [実測] `trial_registry.py` の変更はD1342の射程外なので却下する。

- [実測] campaign/admissionからadapterを直接importする案はmeta-testに抵触する。`orchestrator/tests/test_s8b_attempt_registry.py:1553-1599`

- [実測] `RESULT_SCHEMA` の単純v5置換はv4をstats/holdout/ratifiedの3面で拒否するため却下する。

- [実測]空のrecovery authorityや存在しないclassification authorityを任意literalで埋める案は、新しいtrust rootを無裁定で作るため却下する。

- [実測] campaign retry ordinalをregistry `attempt_ordinal`へそのまま写す案は、cell-wide軸とrepetition内軸を混同し、通常failure後のretryを現coreが拒否するため却下する。`s8b_floor_campaign.py:6169-6187`, `attempt_registry_core.py:1081-1119`

- [実測] proof fieldをoptionalにして「存在すれば比較」する案は、artifact/producer双方のfield削除で恒真化するため却下する。

## 赤になる既存 test

| 区分 | test / fixture | file:line | 理由 |
|---|---|---:|---|
| [実測] 直接 | `test_s8b_profile_closes_slot_binding_budget_and_reason_policy` | `test_attempt_registry_core_s8b_profile.py:296-355` | genesis `root_path` が旧path literal |
| [実測] 直接 | `test_genesis_is_create_only_and_rejects_alternate_or_symlinked_paths` | `test_s8b_attempt_registry.py:1012-1061` | template formatとpublic `registry_path()`署名が変わる |
| [実測] 直接 | `test_new_registry_directories_fsync_each_parent_entry` | `test_s8b_attempt_registry.py:1296-1325` | protocol directoryが1段増える |
| [実測] 直接 | `test_floor_campaign_directly_reexports_shared_leaf_objects` | `test_s8b_floor_contract.py:164-181` | v4 literal pin |
| [実測] 直接 | `test_result_v4_key_contract_is_mode_conditional_and_exact` | `test_s8b_floor_contract.py:366-383` | schema別v4/v5 key集合へ変わる |
| [実測] 直接 | `test_pure_verifier_rejects_legacy_result_schema` | `test_s8b_floor_stats.py:1321-1325` | v4がlegacy rejectionではなくpositive readableになる |
| [実測] 直接 | `test_official_result_rejects_perf_preflight_receipt_fail_closed` | `test_s8b_floor_campaign.py:6040-6075` | direct `assemble_result()` にrequired proofがない |
| [実測] 直接 | `test_official_degraded_result_records_strict_perf_observation` | `test_s8b_floor_campaign.py:6085` | 同上 |
| [実測] 直接 | `test_producer_rejects_incomplete_binary_coverage[...]` | `test_s8b_floor_campaign.py:12838-12855` | required proof追加が既存binary rejectionより先にTypeErrorを起こす |
| [実測] 直接 | recovery registry helper群 | `test_s8b_holdout_admission.py:1900-1998`, `test_s8b_floor_campaign.py:10943-11035` | templateへprotocol引数が必要 |
| [実測] transitive | `_run_campaign()` completion族 | `test_s8b_floor_campaign.py:751-768` | file内call siteは144件。launcher配線、authority不足、v5 proof不在が共有helper経由で波及 |
| [実測] transitive | `candidate_repository()` | `s8b_v2_freeze_fixture.py:337-475` | current定数がv5になるがproof/live registryがない |
| [実測] transitive | `_build_independent_launch_repo()` | `test_s8b_ratified_verify.py:459-617` | v5 fieldとlive registryがない |
| [実測] transitive | `build_production_emitter_g1()` / g2 | `test_s8b_ratified_freeze.py:966-1086,1202-1265` | producerがS3 blockerで止まり、fixture再構築もregistryを作らない |
| [実測] transitive | bespoke holdout candidate fixture | `test_s8b_holdout_freeze.py:1694-1759` | current-v5 proof欠落 |
| [実測] transitive | floor evidence fixture | `s8b_floor_evidence_fixture.py:183-351` | holdout evidenceだけを作り、attempt registryを作らない |

## テスト計画

### 正例

- [推測] `test_s8b_attempt_registry.py::test_protocol_generations_use_distinct_paths_under_one_freeze`
  同じfreeze、異なるprotocol SHAの2 genesisが別pathへ作成されることを確認する。

- [推測] `test_s8b_attempt_registry.py::test_freeze_budget_replay_allows_total_at_limit_across_protocol_generations`
  世代別local countではなく合計がcapちょうどまで通ることを確認する。

- [推測] `test_s8b_floor_attempt_launcher.py::test_current_measurement_generation_marker_launches_one_planned_attempt`
  current marker schemaからreserve、capture、terminalまで到達させる。

- [推測] `test_s8b_holdout_admission.py::test_attempt_registry_capture_returns_full_binding_positive_count_and_tail_head`
  producer captureがfull valid registryの正のNとheadを返す。

- [推測] `test_s8b_ratified_verify.py::test_v5_prefix_proof_survives_valid_later_append`
  artifact capture後にvalid rowをappendしても先頭N行のheadが一致する。

- [推測] `test_s8b_ratified_verify.py::test_historical_reverify_accepts_v4_without_attempt_registry`
  inspectorを呼ばれたらfailするstubにし、v4非遡及を固定する。

- [推測] `test_end_to_end_golden_floor_values_and_tamper_detection` と `test_verify_floor_artifact_binaries_positive_and_negative` をv5正例へ更新する。`test_s8b_floor_campaign.py:9231,12918`

### 向き別の負例

| 向き | test node案 | 恒真化を避ける理由 |
|---|---|---|
| [推測] artifact側欠落 | `test_s8b_floor_stats.py::test_verify_v5_rejects_missing_attempt_registry_with_valid_live_proof` | live proofは正常に与え、v5 exact field欠落だけを変える |
| [推測] producer側削除 | `test_s8b_floor_campaign.py::test_v5_producer_field_deletion_creates_no_pending_result` | 実registryを先に作り、assembly後のfield削除だけを注入しpending不在まで見る |
| [推測] live台帳不在 | `test_s8b_ratified_verify.py::test_v5_reverify_rejects_missing_live_attempt_registry` | artifact proofは変更せず、live fileだけを除く |
| [推測] 報告head改竄 | `test_s8b_floor_stats.py::test_verify_v5_rejects_reported_prefix_head_tamper` | shape-validな別SHAへ変え、live prefixは正常のままにする |
| [推測] live台帳改竄 | `test_s8b_holdout_admission.py::test_attempt_registry_prefix_rejects_live_row_chain_tamper` | artifactを固定し、先頭N行内のrow/hashだけを変える。部品検査として登録する |
| [推測] 別freezeの台帳 | `test_s8b_ratified_verify.py::test_v5_reverify_rejects_registry_bound_to_other_freeze` | canonical expected pathにcore-validな別freeze genesisを置き、binding gateだけを発火させる |
| [推測] v4 downgrade | `test_s8b_holdout_freeze.py::test_new_candidate_rejects_v4_after_v5_cutover` | historical v4正例を別nodeで緑に保ち、新規candidate入口だけを検査する |
| [推測] 予算の世代リセット | `test_s8b_attempt_registry.py::test_second_protocol_cannot_reset_freeze_budget` |第1世代でcapを使い切り、第2世代local count 0のvalid slotをreserveして横断gateだけを発火させる |

- [実測] 束縛負例はartifact欠落、producer削除、live不在、reported head、別freeze、v4 downgradeである。live row chain tamperと非canonical JSONLはregistry部品検査として別分類にする。

## 変異事前登録の候補

| ID | 変異位置 | 変異 | KILLするnode | 帰属確認 |
|---|---|---|---|---|
| [推測] M1 | `s8b_attempt_profile.py:380-382` | pathから`{protocol_sha256}`を除く | `test_protocol_generations_use_distinct_paths_under_one_freeze` | 2入力は各々core-validで、前段拒否なし。赤理由は第2世代のpath衝突だけ |
| [推測] M2 | `s8b_attempt_registry.py:1003-1017` 周辺 | other generationのcountsをcandidate replayへ渡さない | `test_second_protocol_cannot_reset_freeze_budget` | 第2世代local countはcap未満で、既存local gateは拒否しない。横断gateだけが差になる |
| [推測] M3 | `s8b_holdout_admission.py:4969-4990` 隣の新prefix inspector | `len(live)==N` またはlive tail一致を要求する | `test_v5_prefix_proof_survives_valid_later_append` | prefixもappend rowもvalidで、他層の拒否条件はない |
| [推測] M4 | `s8b_floor_stats.py:759-768` 隣の新proof比較 | reported/live比較を削除 | `test_verify_v5_rejects_reported_prefix_head_tamper` | 両proofはshape-validで、別のshape/binding gateは拒否しない |
| [推測] M5 | `s8b_floor_stats.py:1036-1082` | v5でlive registry inspectorを呼ばずreported proofを流用 | `test_v5_reverify_rejects_missing_live_attempt_registry` | artifact自体はvalidで、live不在を拒否できるのはこのI/O gateだけ |
| [推測] M6 | `s8b_holdout_freeze.py:1435-1440` | new candidateのcurrent-v5等値をreadable v4/v5へ緩和 | `test_new_candidate_rejects_v4_after_v5_cutover` | v4 artifactを現行v4規則でvalidに作り、この発行境界だけを発火させる |
| [推測] M7 | `s8b_ratified_freeze.py:2385-2390` | historical readableからv4を除く | `test_historical_reverify_accepts_v4_without_attempt_registry` | v4 fixtureは現行受理規則を満たし、registry inspectorも呼ばないためschema membershipだけが赤理由 |
| [推測] M8 | `s8b_floor_contract.py:340-397` 隣のproof validator | `row_count > 0` を `>= 0` へ緩和 | `test_verify_v5_rejects_zero_row_registry_proof` | exact keyとdigest shapeを全てvalidにし、正数gateだけを変える |

- [実測] producer field削除は後段v5 exact-key gateも同じ入力を拒否するため、mutation候補には登録しない。

- [実測] event hash再計算削除はchain previous/index/canonical検査と重なり、単一理由へ帰属できないため登録しない。

- [実測] binding比較削除はpath選択、genesis full binding、pure proof比較が重なるため登録しない。

- [実測] S3のlauncher呼出し削除変異は、現状authority/ordinal/marker blockerでbaseline自体が到達不能なので、blocker解消前には登録しない。

## 実装単位の分割

- [推測] briefのA/B/Cは採らない。`s8b_holdout_admission.py` がS3 input投影とS4 read-only inspectorの両方を所有し、briefのB/C間でpath ownershipが重なるためである。

- [推測] 次の4単位を推す。編集pathは相互に素である。

1. [推測] 単位A: registry storage、世代、budget、必要なordinal prerequisite

   - `orchestrator/campaign/attempt_registry_core.py`
   - `orchestrator/campaign/s8b_attempt_profile.py`
   - `orchestrator/campaign/s8b_attempt_registry.py`
   - `orchestrator/tests/test_attempt_registry_core_s8b_profile.py`
   - `orchestrator/tests/test_s8b_attempt_registry.py`

2. [推測] 単位B: admission-owned identity、current marker、read-only prefix inspector

   - `orchestrator/campaign/s8b_holdout_admission.py`
   - `orchestrator/tests/s8b_floor_evidence_fixture.py`
   - `orchestrator/tests/test_s8b_holdout_admission.py`

3. [推測] 単位C: trusted launcherとcampaign測定seam

   - `orchestrator/campaign/s8b_floor_attempt_launcher.py`
   - `orchestrator/campaign/s8b_floor_campaign.py`
   - `orchestrator/tests/test_s8b_floor_attempt_launcher.py`
   - `orchestrator/tests/test_s8b_floor_campaign.py`

4. [推測] 単位D: v4/v5 contractと全consumer、共有fixture

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

- [推測] 依存順は authority/ordinal裁定を先に確定し、`A → B → C`、`A+B → D` とする。CとDはB完了後に並行可能だが、D1341により4単位は同一commitでのみlandする。

## 親 brief への異議

- [実測] **P1-aは成立する。** `protocol_sha256` はfixed bytesとcanonical protocol双方で照合され、bindingにも既存fieldとして存在する。`s8b_floor_campaign.py:470-481,7166`, `s8b_holdout_admission.py:691-736`

- [実測] **P1-bは半分だけ成立する。** 新lock規約は不要だが、「coreの既存replayを広げるだけ」ではない。filesystem世代集合の権威、directory shape検査、lock内enumeration、candidateとの二回replayがadapterへ必要である。`s8b_attempt_registry.py:451-490,984-1048`

- [実測] **P1-cは成立しない。** production recovery authority 0件、classification authority source 0件、run-start receipt fieldなし、current marker非互換、retry ordinal意味不一致がある。`s8b_holdout_admission.py:93-109,389-403,4435-4546`, `s8b_floor_campaign.py:6000-6007,6169-6187`, `s8b_attempt_registry.py:1458-1509`

- [実測] **P1-dは成立しない。** 必須編集面はproduction 10 file、test/support 13 file、合計23 pathである。主要な直接影響spanだけでも、`s8b_attempt_registry.py:451-490,984-1048`、`s8b_holdout_admission.py:4960-4990`、`s8b_floor_campaign.py:5723-5777,5995-6165,6485-6635`、`s8b_floor_stats.py:682-768,1036-1082`、`s8b_holdout_freeze.py:1424-1440`、`s8b_ratified_freeze.py:2333-2390,3253-3302` の合計772 existing LOCに及ぶ。これは新規inspector、横断replay、test追加を含まない下限である。

- [推測] actual diffはblocker prerequisiteを含めて600から900 changed LOC以上になる可能性が高く、4 sub-featureを通常の1 waveで安全に実装、変異、reviewする規模ではない。

- [実測] **P1-eは指定worktree内について成立する。** repo内registry artifactは0件なので移動も書換えも不要である。ただしGit common dir配下など指定worktree外の実在へは一般化しない。

- [実測] briefはcurrent measurement-generation consumption markerとadapterのlegacy marker期待値の不一致を落としている。`s8b_holdout_admission.py:4435-4546`, `s8b_attempt_registry.py:55-68,1458-1509`

- [実測] briefはcampaign retry ordinalとregistry primary ordinalの意味差を落としている。この不足を解かずにS3を配線するとplanned以外の正当retryが停止する。`s8b_floor_campaign.py:6169-6187`, `attempt_registry_core.py:1081-1119`

## 総括

- [実測] S1は `{freeze_sha256}/{protocol_sha256}`、S2はadapter-owned enumerationと既存root lock内のcross-generation replay、S4はv5-only新規発行とv4/v5 historical reader、および `{N, head_at_N}` prefix比較で確定できる。

- [実測] S3は現 briefのまま到達不能である。authority 2種、run-start receipt、current marker handoff、retry ordinal軸を推測で埋めてはならない。

- [実測] D1341によりS1/S2/S4だけを先行landしてはならない。推奨はS3不足事項を同じland単位の明示的 prerequisiteとして再briefし、その確定後に4実装単位を進めることである。

- [実測] pytestは未実走であり、緑は報告しない。