## 結論

静的照合の結論は次のとおりです。

- §J の要件 9〜18を一括実装するには、R1〜R4の単純な結線を超える未確定事項があります。特に要件 12 の物理 executor と要件 14 の `campaign.lock` content-addressed ref は、現在の wire contract だけでは実装を一意に決められません。
- 要件 16 は既に実装済みです。要件 17 の native WAL decoder も既に実装済みで、未実装なのは mixed-shape 拒否だけです。
- 親の3単位は production file だけなら排他的ですが、共有 fixture、originless compatibility test、A が C の completion API 確定後に `trial_registry.py` へ戻る順序が未定義です。現状のままの並列3着手は避けるべきです。
- 推奨する意味のある切断点は、第一 wave で要件 9〜11・13〜17の identity/evidence contract を固定し、第二 wave で要件 12・18と R2 completion を実装する形です。第一 wave だけを land した時点では「8c結線完了」と名乗れません。
- 以下の行番号は、この worktree で静的確認した現行位置です。編集、pytest、commit は行っていません。

## 受入要件 9

33個の `cfg_q`、preimage、identity は `p3_autonomous_workload_trial.py` の producer が導出し、`reflux_origin_topology.py` は変更しません。

変更位置:

- `orchestrator/campaign/p3_autonomous_workload_trial.py:407-415`
  - 次の内部型を追加します。

```python
@dataclasses.dataclass(frozen=True, slots=True)
class OriginCampaignRun:
    query_ordinal: int
    campaign: CampaignConfig
    identity_preimage: str
    campaign_run_identity: str
```

- `orchestrator/campaign/p3_autonomous_workload_trial.py:1199` 直後
  - 次の2関数を新設します。

```python
def _derive_origin_campaign_run(
    logical_cfg: CampaignConfig,
    *,
    attempt_capability_sha256: str,
    query_ordinal: int,
) -> OriginCampaignRun
```

```python
def _derive_origin_campaign_runs(
    logical_cfg: CampaignConfig,
    *,
    attempt_capability_sha256: str,
) -> tuple[OriginCampaignRun, ...]
```

処理は次に固定します。

- 論理 cfg の `search_config` に `origin_campaign_run` が既にあれば拒否。
- `query_ordinal` は exact `int` の `0..32`。
- `dataclasses.replace(logical_cfg, search_config={..., "origin_campaign_run": {"attempt_capability_sha256": ..., "query_ordinal": q}})`。
- `ident.canonical_preimage(cfg_q)` と `str(ident.campaign_id(cfg_q))` を同じ helper で計算。
- 33件について、q順、preimage相異、identity相異を envelope 構築前に検査。
- 時刻、PID、乱数、`trial` 接尾辞は使用しない。

- `orchestrator/campaign/p3_autonomous_workload_trial.py:1518-1526`
  - `_prepare_origin_trial_runtime()` が作った物理成分なしの `PreparedCampaignIdentity` を `OriginTrialRuntime` に保持します。

既存署名の変更はありません。

影響する既存 test:

- `orchestrator/tests/test_p3_autonomous_workload_trial.py:8175`
- 同 `:10280-10323`。現在の `fixture-run-0000` 自己申告 helper は producer導出へ置換。
- `orchestrator/tests/test_reflux_origin_topology.py:123-139` は topology 自身の33相異 gate として維持。

新規 test は `test_p3_autonomous_workload_trial.py` の origin test 群 `:10712` 以降へ置きます。

- 同じ入力から2回導出して完全一致。
- qだけが違う33件の preimage/identity が相異。
- slot capability digestが違えば全identityが変わる。
- q固定0変異が envelope 作成前に拒否される。
- 論理 cfg に既存 `origin_campaign_run` がある場合は上書きせず拒否。

## 受入要件 10

registry照合と origin capability発行は、現行の論理 `PreparedCampaignIdentity` のまま維持します。

変更位置:

- `orchestrator/campaign/p3_autonomous_workload_trial.py:1329-1342`
  - `_trial_launch_admission()` の `assert_campaign_binding(... actual_campaign_id=prepared.campaign_id)` は変更しません。
- 同 `:1518-1555`
  - `_prepare_origin_trial_runtime()` が論理 `prepared_campaign` を `issue_origin_binding_capability()` へ渡す順序を維持。
- 同 `:4628-4639`
  - 物理identity導出は `_reserve_registered_attempt_slot()` の戻り値取得後へ置きます。上記2照合より前へ移動してはいけません。
- `orchestrator/campaign/trial_registry.py:4998-5010`
  - `assert_campaign_binding()` の署名・比較述語は変更しません。

```python
def assert_campaign_binding(
    binding: TrialBinding,
    *,
    arm_execution: TrialArmExecutionBinding,
    actual_campaign_id: str,
) -> None
```

新規負例:

- `test_p3_autonomous_workload_trial.py` で `cfg_q` の identity を `assert_campaign_binding()` へ渡し、`[campaign-binding]` で拒否。
- capability issuer を spy し、受け取った `prepared_campaign.campaign.search_config` に `origin_campaign_run` が無いことを検査。
- identity導出を capability発行より前へ移す変異を呼出順 test で拒否。

## 受入要件 11

現在は envelope が observation開始後の `_run_workload()` 内で書かれています。

- `begin_attempt_observation`: `p3_autonomous_workload_trial.py:4675`
- envelope write: 同 `:3811-3816`

この順序を次へ変更します。

```text
capability発行
-> attempt slot予約
-> initial ledger snapshot読取り
-> 33物理identity導出
-> RecoveryEnvelope構築
-> run_root/origin作成
-> envelope create-only書込み、read-back
-> lifecycle startへdigest束縛
-> begin_attempt_observation
-> executor
```

変更位置:

- `orchestrator/campaign/p3_autonomous_workload_trial.py:429-438`
  - callerが完成済み `RecoveryEnvelope` を渡す現行 `OriginProducerInputs.run_plan` を廃止。
  - identityを含まない入力型を追加します。

```python
@dataclasses.dataclass(frozen=True, slots=True)
class OriginMemberPlanInput:
    candidate_salt: str
    result_evidence_salt: str
    constraint_salt: str
    evidence_path: str
```

```python
@dataclasses.dataclass(frozen=True, slots=True)
class OriginRunPlanInput:
    hypothesis_sha256: str
    validation_plan_sha256: str
    attempt_0_batch_id: str
    retry_1_batch_id: str
    event_operation_ids: reflux_origin_topology.EventOperationIds
    source_mask: int
    member_materials: tuple[OriginMemberPlanInput, ...]
```

`OriginProducerInputs` は次の field 変更になります。

```python
# before
run_plan: reflux_origin_topology.RecoveryEnvelope

# after
run_plan_input: OriginRunPlanInput
```

他の `result_record_bytes`、`evidence_root`、`verifier_policy_bytes`、`generator_closure`、`terminal_operation_id`、`enforcement_arm` は維持します。

- `orchestrator/campaign/p3_autonomous_workload_trial.py:1439` より前
  - 次を新設します。

```python
def _build_origin_recovery_envelope(
    *,
    capability: reflux_origin_binding.OriginBindingCapability,
    source_closure: ValidatedSourceClosure,
    initial_snapshot: reflux_origin_ledger.OriginSnapshot,
    run_plan_input: OriginRunPlanInput,
    campaign_runs: tuple[OriginCampaignRun, ...],
) -> reflux_origin_topology.RecoveryEnvelope
```

この関数だけが `MemberRecoveryMaterial.planned_campaign_run_identity` を埋め、既存 `build_recovery_envelope()` を呼びます。callerから identity を受けません。

- `orchestrator/campaign/p3_autonomous_workload_trial.py:3811-3816`
  - envelope writeを削除。
- 同 `:4624-4697`
  - `_assert_reservation_preflight()` の戻り値を保持し、slot予約後に上記順序を実装。
- 同 `:4751-4767`
  - origin branchで先行作成済みの `run_root` を再作成しないよう分岐。originlessの作成順は維持。

R1側の変更:

- `orchestrator/campaign/trial_registry.py:204-220`

```python
_LIFECYCLE_START_BASE_KEYS = frozenset({...現行14 key...})
_LIFECYCLE_START_KEYS = frozenset({
    _LIFECYCLE_START_BASE_KEYS,
    _LIFECYCLE_START_BASE_KEYS | {"origin_run_plan_sha256"},
})
```

- 同 `:4420-4427`
  - startもterminalと同様に `frozenset(value) in _LIFECYCLE_START_KEYS` で検査。
- 同 `:382-416`
  - `TrialLifecycleToken` と `_TrialLifecycleCapabilityState` に `origin_run_plan_sha256: str | None` を追加。
- 同 `:4634-4645`

変更前:

```python
def record_trial_start_once(
    *,
    admission: TrialLaunchAdmission,
    effective_preregistration: EffectivePreregistration | None,
    manifest_path: Path,
    run_root: Path,
    repository_root: Path,
    attempt_slot: AttemptSlotCapability,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    lifecycle_path: Path = DEFAULT_LIFECYCLE_PATH,
    origin_binding: OriginBindingCapability | None = None,
) -> TrialLifecycleToken
```

変更後:

```python
def record_trial_start_once(
    *,
    admission: TrialLaunchAdmission,
    effective_preregistration: EffectivePreregistration | None,
    manifest_path: Path,
    run_root: Path,
    repository_root: Path,
    attempt_slot: AttemptSlotCapability,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    lifecycle_path: Path = DEFAULT_LIFECYCLE_PATH,
    origin_binding: OriginBindingCapability | None = None,
    origin_run_plan_sha256: str | None = None,
) -> TrialLifecycleToken
```

`origin_binding is None` と digest不在を同値にし、originlessでは key自体を出しません。

影響する既存 test:

- `test_trial_registry.py:3949-4176`
- 同 `:4180-4243`
- `test_p3_autonomous_workload_trial.py:10280-10323`
- 同 `:10712-10797`
- `test_reflux_originless_compatibility.py:515-548`
- 同 `:1189-1298`

新規 test:

- envelope writeが `begin_attempt_observation` より前。
- create-only write失敗時に observation未開始。
- start rowのdigestが実bytesのsha256と一致。
- origin bindingあり/digestなし、digestあり/origin bindingなしを双方拒否。
- caller由来の planned identity を受けるAPIが存在しないことを signature testで固定。

## 受入要件 12

変更箇所自体は明確です。

- `orchestrator/campaign/p3_autonomous_workload_trial.py:3804-3850`
  - `layout` 作成より前、かつ generation loopより前で origin分岐。
- 同 `:2809-2824`
  - `_assert_reservation_preflight()` の `ReservationCheck` を捨てず `OriginTrialRuntime` に保持。
- `orchestrator/campaign/p3_s4_loop_trigger_gating.py:734-860`
  - `_run_one_iteration_resolved()` の下に origin専用entry pointを新設。
- `drive_iteration()` `:984-1162` は変更せず、origin executorから呼ばない。

必要な公開境界案:

```python
def drive_origin_topology_member(
    *,
    campaign_cfg: CampaignConfig,
    perf: PerfConfig,
    member: reflux_origin_topology.TopologyMember,
    planner: L.PlannerProposal,
    auditor: AuditorVerdict,
    sub: str,
    layout: CampaignLayout,
    cache_root: str,
    proposal_path: str,
    build_context: BuildRunContext,
) -> dict
```

任意 `drive` callbackは受けません。関数内部で次を行います。

- `member.candidate_wire` から `CoderProposalTriggerGating` を構築。
- `_assert_layout_matches_campaign(... require_authoritative_root=True)`。
- `_assert_resume_allowed()`。
- `_run_one_iteration_resolved()`。
- `CampaignSummary.campaign_id` 由来の戻り値を返し、plan値をactualへ複写しない。
- `drive_iteration()` 末尾の通常 `CERTIFIED_ACCEPTANCE` admissionは実行しない。

producer側:

```python
def _execute_origin_topology(
    *,
    runtime: OriginTrialRuntime,
    workload: str,
    perf: PerfConfig,
    providers: Mapping[str, Any],
    journal: AttemptJournal,
    run_root: Path,
    sub: str,
    cache_root: str,
    started_monotonic: float,
    max_wall_s: int,
    build_context: BuildRunContext,
) -> dict[str, Any]
```

各qで以下を要求します。

- `layout_q = exploration_campaign_layout(campaign_run_identity)`.
- `_assert_fresh_campaign_state(layout_q)`.
- cfg再導出identityとplan一致。
- `drive_origin_topology_member()` のactual campaign IDとplan一致。
- 前qのevidenceがfsync/read-back済み。
- `ReservationCheck.ensure_remaining()` 成功後だけ実行。
- 同一process内失敗だけをtombstone suffixへ変換。

ただし、この署名を最終確定する前に段4裁定が必要です。現在の設計には次がありません。

- generation loopを使わずに、各mask用の mandatory auditor verdictをどこで発行するか。現行 `_quarantine_and_audit()` は `planner` と `auditor` を必須にします (`p3_s4_loop_trigger_gating.py:522-568`)。
- source candidateを manifestの `generations == 2` のどちらから選ぶか。
- `ensure_remaining()` に渡す1 member当たりの批准済み保守上限。設計は必要性だけを述べ、値を定めていません。
- result-evidence writerとqualifying rejection normalizerがscope外のまま、次qへ進んでよいdurable evidenceを誰が返すか。

したがって要件 12 は、現 briefのまま実装方法を一意に決められません。

影響する既存 test:

- `test_p3_autonomous_workload_trial.py:2428-2607`
- 同 `:3122-3245`
- 同 `:10712-10925`
- `test_p3_s4_loop_trigger_gating.py:906-1001`
- 同 `:1164-1238`
- 同 `:2614-2743`

新規 test:

- origin pathが generation loopへ入らない。
- q0 layout再利用を拒否。
- q別fresh/resume checkが33回。
- fake summaryが別campaign IDを返した場合に拒否。
- plan値をactualとして複写する変異を拒否。
- q前の残時間検査が33回で、不足q以降だけtombstone。
- public callerがdrive callbackを差し替えられない。

## 受入要件 13

`execution-provenance/v2` は `campaign_run_identity` を加えたexact 8 keyとします。v1 decoderは作りません。

変更位置:

- `orchestrator/campaign/reflux_result_evidence.py:124-132`
  - `_EXECUTION_PROVENANCE_KEYS` に `campaign_run_identity` を追加。
- 同 `:551-591`
  - schemaを `execution-provenance/v2` のみへ変更。
  - `build_attempt_id`、論理 `campaign_id`、物理 `campaign_run_identity`、`workload` を非空文字列として検査。
- 同 `:34-59`
  - production writer用の関数をexport。

```python
def execution_provenance_v2_record(
    *,
    build_attempt_id: str,
    campaign_id: str,
    campaign_run_identity: str,
    workload: str,
    contract_sha256: str,
    trigger_binding: Mapping[str, object],
    execution_receipt_sha256: str,
) -> dict[str, object]
```

```python
def write_execution_provenance_v2_create_only(
    *,
    evidence_root: Path,
    relative_path: Path,
    record: Mapping[str, object],
) -> Path
```

- `orchestrator/campaign/reflux_formal_consumer.py:687-724`
  - 既存FC03は次を維持。

```python
provenance["campaign_id"]
== trial["campaign_id"]
== capability.campaign_id
```

  - `campaign_run_identity` は別の物理identity比較へ追加し、FC03の論理値を置換しません。

fixture変更:

- `orchestrator/tests/reflux_origin_fixture_builder.py:409-420`
  - v2と物理identityを生成。
- 同 `:611-663`
  - q別 provenanceへq別物理identityを入れる。
- `orchestrator/tests/reflux_origin_fixture_baseline.json:7-9,23-25`
  - 新canonical bytesへ更新。

影響する既存 test:

- `test_reflux_result_evidence.py:81-101`
- 同 `:192-208`。現在はv2をwrong-versionとしているため、v1をwrong-versionへ反転。
- `test_reflux_formal_consumer.py:512-555`
- `test_reflux_origin_fixture_builder.py:107-119,163-225,301-326`
- `test_p3_autonomous_workload_trial.py:10349-10387`

新規 test:

- v2 exact 8 key正例。
- `campaign_run_identity` 欠落・extra key・v1を拒否。
- FC03の3項等式を物理値へ置換した変異を拒否。
- 物理identityが変わっても論理campaign IDを書き換えないことを確認。

## 受入要件 14

formal consumerに物理 `campaign.lock` の解決と再導出を追加します。

推奨関数:

```python
def _validate_physical_campaign_bindings(
    *,
    capability: OriginBindingCapability,
    attempt_capability_sha256: str,
    run_plan: RecoveryEnvelope,
    paired: Sequence[_MemberRecord],
    resolved: Sequence[ResolvedResultEvidence],
) -> None
```

配置は `orchestrator/campaign/reflux_formal_consumer.py:687` の前です。`evaluate_formal_origin()` の呼出順は次にします。

```text
content-addressed resolve
-> execution provenance FC03
-> physical campaign lock再導出
-> FC05a/FC05b/FC05c
-> topology/outcome
```

検査内容:

- qごとの `campaign.lock` をsymlink拒否、digest一致で解決。
- `campaign_lock.decode_campaign_lock_bytes()` でdecode。
- `search_config["origin_campaign_run"]` のexact keyを
  `attempt_capability_sha256/query_ordinal` に固定。
- qがledger record、run plan、provenanceと一致。
- lock preimageから物理identityを再導出し、run planとprovenanceへ一致。
- `origin_campaign_run` を除いた論理preimageを再構成し、`capability.campaign_id` と一致。
- `ordered_wal.source_wal_ref` が同じ物理rootの exact `runs/wal.jsonl` を指すこと。
- q10/q11のroot/config交換を、FC05a〜cとは独立して拒否。

ただし、現wireには `campaign.lock` の content-addressed refを置く場所がありません。

- `reflux_result_evidence.py:112-115` の `evidence` は2 ref exact。
- provenance v2は要件13で8 keyに確定し、8番目は `campaign_run_identity`。
- report `campaign_runs` は要件18でexact 3 keyです。

段4では次を裁定する必要があります。

推奨は `result-evidence/v2` を新設し、`evidence` を次のexact 3 refにする案です。

```python
{
    "ordered_wal_ref",
    "execution_provenance_ref",
    "campaign_lock_ref",
}
```

これを採る場合の追加変更:

- `reflux_result_evidence.py:62,76-132,223-314`
  - `result-evidence/v2` を新規生成schemaにする。
- 同 `:167-174`
  - `ResolvedResultEvidence` に次を追加。

```python
campaign_lock_ref: ResolvedEvidenceBytes
campaign_lock: campaign_lock.DecodedCampaignLock
```

- 同 `:673-704`
  - 第3 refを解決してdecode。
- 実在する `result-evidence/v1` corpusの有無は今回の射影資料では確認されていないため、v1 decoderの要否は別途実測が必要です。

このcarrier追加を拒否する場合、§Dの「content-addressed refとして解決」は満たせず、要件14を完了扱いにできません。

新規 testは `test_reflux_formal_consumer.py` に置きます。

- q10/q11のlock ref、root、provenanceを整合的に交換し、FC05a〜cを通した上で物理identity gateだけが赤。
- lock内qだけ変更。
- slot capability digestだけ変更。
- WAL refを別layoutへ向ける。
- lock refのdigest、symlink、root escapeを拒否。

## 受入要件 15

formal consumerはin-memory planだけでなく、lifecycle startに束縛されたdigestで固定pathのenvelopeを再読します。

新設関数:

```python
def _resolve_bound_recovery_envelope(
    *,
    run_root: Path,
    run_plan: RecoveryEnvelope,
    origin_run_plan_sha256: str,
) -> None
```

配置:

- `orchestrator/campaign/reflux_formal_consumer.py:544` の前。
- fixed pathは `<run_root>/origin/recovery-envelope.json`。
- `resolve_content_addressed_ref()` と同じsymlink/root confinementを使う。
- raw digestが `origin_run_plan_sha256` と一致。
- raw bytesが `canonical_recovery_envelope_bytes(run_plan)` と完全一致。

`evaluate_formal_origin()` の署名変更:

変更前、`reflux_formal_consumer.py:979-995`:

```python
def evaluate_formal_origin(
    *,
    capability: OriginBindingCapability,
    source_closure: ValidatedSourceClosure,
    run_plan: RecoveryEnvelope,
    authority_blob_bytes: bytes,
    launch_admission_record_sha256: str,
    origin_snapshot: ledger.OriginSnapshot,
    sealed_batches: Sequence[ledger.SealedBatch],
    result_record_bytes: Sequence[bytes],
    evidence_root: Path,
    verifier_policy_bytes: bytes,
    enforcement_arm: str,
    arm_binding_digest_sha256: str,
    generator_closure: Mapping[str, object],
    operation_id: str,
) -> FormalConsumerResult
```

変更後:

```python
def evaluate_formal_origin(
    *,
    capability: OriginBindingCapability,
    source_closure: ValidatedSourceClosure,
    run_plan: RecoveryEnvelope,
    run_root: Path,
    origin_run_plan_sha256: str,
    attempt_capability_sha256: str,
    authority_blob_bytes: bytes,
    launch_admission_record_sha256: str,
    origin_snapshot: ledger.OriginSnapshot,
    sealed_batches: Sequence[ledger.SealedBatch],
    result_record_bytes: Sequence[bytes],
    evidence_root: Path,
    verifier_policy_bytes: bytes,
    enforcement_arm: str,
    arm_binding_digest_sha256: str,
    generator_closure: Mapping[str, object],
    operation_id: str,
) -> FormalConsumerResult
```

producer側:

- `p3_autonomous_workload_trial.py:1632-1680`

変更前:

```python
def _complete_origin_runtime(runtime: OriginTrialRuntime) -> None
```

変更後:

```python
def _complete_origin_runtime(
    runtime: OriginTrialRuntime,
    *,
    run_root: Path,
    lifecycle_token: trial_registry.TrialLifecycleToken,
    attempt_slot: trial_registry.AttemptSlotCapability,
) -> None
```

lifecycle tokenの `origin_run_plan_sha256` とattempt slotの `capability_digest_sha256` をformal consumerへ渡します。

新規 test:

- disk envelopeをstart後に変更すると拒否。
- 同じin-memory objectでも別pathなら拒否。
- digestだけ別値なら拒否。
- fixed path以外へのcaller指定を受ける引数が存在しない。
- originless pathはこのresolverを一度も呼ばない。

## 受入要件 16

FC05aの実装は既に存在します。

- `orchestrator/campaign/reflux_formal_consumer.py:768-779`
  - `build_attempt_id` の33相異検査を変更しません。
- `orchestrator/tests/test_reflux_formal_consumer.py:583-597`
  - 既存負例があります。

必要なのは、要件14追加後もこの負例がFC03やlock検査に先取りされないようfixtureを更新することです。

- 33のcampaign lock、physical identity、provenanceは正しいまま。
- q1の `build_attempt_id` だけq0と重複。
- 期待reasonは引き続き `FC05A`。

production変更は不要です。また、禁止されている「provenance 33値相異」の別gateは追加しません。

## 受入要件 17

native WAL decoderは既に実装済みです。

- `orchestrator/campaign/reflux_formal_consumer.py:727-765`
  - exact `variant/stage/env_tag/ts/payload` と `stage="trigger_binding"` を読む。
- `test_reflux_formal_consumer.py:619-688`
  - live producer/native形の正例。
- 同 `:691-802`
  - legacy root、extra key、重複native trigger等の負例。

未実装なのは、native triggerにlegacy root triggerを混ぜたprojectionの明示拒否です。現状 `_wal_trigger()` はlegacy行を無視してnative行だけを採り得ます。

変更案:

```python
def _wal_trigger_shape_family(record: Mapping[str, object]) -> str | None
```

- native triggerなら `"native-stage-payload"`。
- root `kind == "TriggerGateBinding"` なら `"legacy-root"`.
- `_wal_trigger()` はtrigger候補のfamily集合がexact 1でなければ `None`。
- 新規origin evidenceではnative familyだけを受理。
- terminal WALの既存outcome検査は弱めない。

新規 test:

- nativeのみ正例。
- legacyのみ拒否。
- native + legacy mixed拒否。
- native decoderを無効化する変異でlive producer正例が赤。
- legacy候補を無視する変異でmixed負例が赤。

## 受入要件 18

origin reportはcellの論理 `campaign_id` を残し、単数 `campaign_root` を `campaign_runs` に置換します。

producer変更:

- `orchestrator/campaign/p3_autonomous_workload_trial.py:3817-3831`
  - origin branchでは次を出します。

```python
{
    ...共通cell fields...,
    "campaign_id": logical_campaign_id,
    "campaign_runs": [
        {
            "query_ordinal": q,
            "campaign_run_identity": identity,
            "campaign_root": root,
        }
        for q in range(33)
    ],
}
```

- origin cellでは `campaign_root` key自体を出しません。
- originless cellは現行 `campaign_root` を維持。

completion用の新規公開関数:

```python
def assert_origin_trial_completion(
    *,
    report: Mapping[str, Any],
    run_root: Path,
    attempt_capability_sha256: str,
) -> None
```

配置は `orchestrator/campaign/autonomous_trial_completeness.py:1301` の前を推奨します。検査は次です。

- 発火条件は `report["launch_admission"]["origin_binding"]` の存在だけ。
- issued capabilityはproducer時点ではexact objectで再検査。
- `origin_terminal_projection.formal_receipt_sha256` が非null。
- `campaign_runs` exact 33件、各exact 3 key、qが `0..32` 昇順。
- identityとrootが相異。
- 各lockの `origin_campaign_run.attempt_capability_sha256` が引数と一致。
- 各lockとWALを再読し、root、identity、qを再導出。
- 通常の「全campaign admitted」は呼ばない。

`layer3_report.py:659` 前へ、rendererではない読取り専用helperを追加します。

```python
def inspect_origin_campaign_runs(
    *,
    campaign_runs: Sequence[Mapping[str, Any]],
    logical_campaign_id: str,
    attempt_capability_sha256: str,
    output_root: Path,
) -> tuple[dict[str, Any], ...]
```

これは各runのlock/WAL raw digest、ccbench commit、env tagを返します。`build_report()` `:725-901` の受理述語は変更しません。

completeness変更:

- `autonomous_trial_completeness.py:781-899`
  - `_check_cell_campaign_identity()` はoriginless専用のまま維持。
- 同 `:1033-1231`
  - `_check_arm_digest_chain()` でorigin branchを追加し、単数root比較を回避。
- 同 `:2023-2169`
  - exact origin bindingをbranch条件に使用。
- 同 `:2531-2584`
  - `_check_cell_metadata()` のrequired keyをorigin/通常のclosed alternativesにする。
- 同 `:2886-2911`
  - origin statusは通常cell admissionではなく `assert_origin_trial_completion()` の条件で決める。
- 同 `:3078-3229`
  - origin専用journal/report検査へ分岐。通常generation state machineへ流さない。
- 同 `:4217-4589`
  - `verify_s8c_cross_binding()` にorigin専用modeを追加し、33 lock/WALを再読。既存build/no-build modeは不変。
- 同 `:4815-5033`
  - `assert_campaign_layer3_chain()` はorigin時に `inspect_origin_campaign_runs()` を呼び、33通常Layer3 admissionを要求しない。

registry変更:

- `trial_registry.py:5605-5744`
  - `_read_acceptance_measurement_targets()` をorigin-awareにし、originでは33runのlock/WAL snapshotと共通ccbench/envを読む。
- 同 `:5811-5813`
  - report snapshot後にorigin materialを保持。
- 同 `:6092-6166`
  - originでは単数 `campaign_root` 走査と6個の通常Layer3 report要求を通らない。
- 同 `:6180-6240`
  - attempt registryを読んだ後、対象slotのclassification rowにある `capability_digest_sha256` を `assert_origin_trial_completion()` へ渡す。
- 同 `:6246-6272`
  - origin lock/WAL snapshotもreceipt発行直前に再読し、途中変更を拒否。

既存の外部署名は維持します。

```python
def assert_autonomous_trial_completeness(
    *, report: Mapping[str, Any], attempt_journal: Path
) -> None
```

```python
def verify_s8c_cross_binding(
    *,
    report: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    run_root: Path,
    output_root: Path | None = None,
) -> dict[str, Any]
```

```python
def assert_campaign_layer3_chain(
    *, report: Mapping[str, Any], output_root: Path
) -> None
```

影響する既存 test:

- `test_autonomous_trial_completeness.py:1033-1231`
- 同 `:2023-2195`
- 同 `:2531-2600`
- 同 `:2886-2911`
- 同 `:3078-3229`
- 同 `:4039-4457`
- 同 `:4815-5033`
- `test_trial_registry.py:1823-2232`
- 同 `:2557-2629`
- 同 `:2811-2840`
- `test_layer3_report.py:2677-2870`
- `test_p3_autonomous_workload_trial.py:10712-10925`

新規 test:

- q8/q9のlist順交換を拒否。
- q8/q9のidentity/root交換をlock再導出で拒否。
- 32件、34件、重複q、重複root、extra keyを拒否。
- origin cellの通常admissionがrejectedでもformal receiptと33run再検査が成立すればcompletionを認める。
- receipt欠落、1 lock欠落、1 WAL変更でpartial。
- originless cellへ `campaign_runs` を足してもorigin branchへ入らず、従来どおり未知形として拒否。

## file所有と単位境界

親案はproduction fileだけを見れば重複していません。しかし成果物全体では要修正です。

理由:

- `test_reflux_originless_compatibility.py` のownerが未定義。
- Unit Cが作るcompletion APIを Unit Aの `trial_registry.py` が呼ぶため、Aを一度で完結できません。
- Unit Cのformal consumer fixtureは Unit Aのfixture builder/schema確定前には編集できません。
- Unit Bのproducerは Unit Aのlifecycle signatureと Unit Cのcompletion signatureの双方に依存します。

排他的なownerを次に固定する案を推奨します。

| 単位 | 排他的owner |
|---|---|
| A: wire contract | `trial_registry.py`、`reflux_result_evidence.py`、`test_trial_registry.py`、`test_reflux_result_evidence.py`、`reflux_origin_fixture_builder.py`、`test_reflux_origin_fixture_builder.py`、`reflux_origin_fixture_baseline.json`、`test_reflux_originless_compatibility.py` |
| B: producer/executor | `p3_autonomous_workload_trial.py`、`p3_s4_loop_trigger_gating.py`、対応する2 test |
| C: consumer/completion | `reflux_formal_consumer.py`、`autonomous_trial_completeness.py`、`layer3_report.py`、対応する3 test |

単位間の公開境界は次に固定します。

```python
# A -> B
record_trial_start_once(..., origin_run_plan_sha256: str | None = None)
    -> TrialLifecycleToken
```

```python
# A -> C
resolve_result_evidence(record: object, *, evidence_root: Path)
    -> ResolvedResultEvidence
```

```python
# C -> A/B
assert_origin_trial_completion(
    *,
    report: Mapping[str, Any],
    run_root: Path,
    attempt_capability_sha256: str,
) -> None
```

```python
# B内部
drive_origin_topology_member(...) -> dict
```

A以外は `trial_registry.py`、fixture builder、originless compatibility testを編集しない形にします。

## 依存順序

実装順は次です。

1. 親の段4で、`campaign_lock_ref` のcarrier、origin auditor/source proposal、1 member保守時間を裁定。
2. Aが lifecycle signature、execution-provenance v2、必要ならresult-evidence v2、fixture wireを固定。
3. CがAの `ResolvedResultEvidence` を使って要件14〜17と `assert_origin_trial_completion()` を実装。
4. BがAの lifecycle APIとCのcompletion APIを使って要件9〜12、report producerを実装。
5. Aが最後に `trial_registry.py` のacceptance側へCのcompletion APIを結線。
6. A ownerがoriginless full-structure testを更新せず再生成比較し、統合差分を検査。

したがって、段5を最初からA/B/C完全並列にはできません。少なくともAのwire contract確定後でなければB/Cを開始できず、Cのcompletion signatureはBより先に固定する必要があります。

## P1〜P5の判定

| 前提 | 判定 | 実測根拠 |
|---|---|---|
| P1: R1〜R4の結線だけが要件9〜18の全体 | 要修正 | §J `docs/phase3-8c-wiring-design.md:885-894` は確かに9〜18を実装waveへ渡しています。しかし現productionはcallerが完成済みrun plan/evidenceを渡すだけ (`p3_autonomous_workload_trial.py:429-438`)、単一layoutとgeneration loop (`:3804-3850`)、generic admitted完了 (`:3544-3562`) です。要件12を満たすauditor/source選択、時間上限、durable evidence producerが未設計です。`reflux_formal_consumer.py:1-8` もP6不在を明記しています。 |
| P2: 3単位のfile所有は排他 | 要修正 | production一覧は排他的ですが、shared fixtureをAが所有しCが消費し、originless compatibility testは未割当です。さらにAのregistry acceptanceがCの新APIへ依存します。上記ownerと順序を明文化すれば排他化できます。 |
| P3: v1歴史decoderを作らない | 正 | production writerは無く、validatorはv1のみ (`reflux_result_evidence.py:551-591`)、唯一の生成点はfixture (`reflux_origin_fixture_builder.py:409-420`) です。D1669の条件どおりfixtureをv2へ移し、origin consumerはv2だけを受理します。 |
| P4: `_run_workload` の単一layout前で分岐しgeneration loopへ入らない | 要修正 | 分岐位置自体は正しく、単一layoutは `p3_autonomous_workload_trial.py:3804-3810`、loopは`:3850`です。ただしloop外でplanner/auditor/source candidateをどう得るかが未確定です。位置は採用し、入力契約を段4で追加決定する必要があります。 |
| P5: 受入はrepo全走 | 要修正 | repo全走は最終回帰として必要でも、単独では要件別変異を証明しません。特にoriginlessの非揮発全構造比較は `test_reflux_originless_compatibility.py:1189-1298`、FC05aは `test_reflux_formal_consumer.py:583-597`、native WALは同`:619-802`の焦点testが必要です。今回は一切実行していません。 |

## waveを分ける場合の中間状態

本waveに要件9〜18全体を入れる場合、`p3_autonomous_workload_trial.py`、completeness、cross-binding、registry acceptanceの大規模な並行変更になります。現時点では分割を推奨します。

第一 wave:

- 要件9〜11。
- R1 lifecycle digest。
- 要件13〜17。
- `campaign_lock_ref` carrierとformal consumerまで。
- originless bytes/受理集合の回帰。
- production executorとorigin completionは未実装と明記し、結線完了を名乗らない。

第二 wave:

- 要件12のsealed executor。
- 要件18のreport/completeness/cross-binding/registry。
- R2 origin専用completion。
- 33runの公開経路正例。

この切り方では、第一 wave終了時に「diskへ束縛されたrun planと、物理lock/WALを検証できるconsumer contract」が成立します。executor未実装のため物理実行を名乗らず、意味のあるfail-closedな中間状態です。

## originless不変の固定方法

具体策は次です。

- 発火条件を常に `launch_admission.origin_binding` のkey存在に限定する。`origin_terminal_projection`、`campaign_runs`、`None` 値から推測しない。
- `run_trial()` `p3_autonomous_workload_trial.py:4399-4426` の既存引数と `None` defaultを維持。
- `_finish_trial()` `:3248-3282`、`_run_workload()` `:3720-3732` のorigin引数はdefault `None`のまま。
- originless reportは単数 `campaign_root`、originless lifecycle startはbase key集合をそのまま出す。
- lifecycle/report schema versionを全経路で一括bumpしない。
- unknown keyを一般許可せず、closed alternativeを追加するだけにする。

固定する検査:

- `test_reflux_originless_compatibility.py:1189-1298`
  - omittedとexplicit `None`を比較。
  - pre-wave非揮発leaf集合との完全一致。
  - report、journal、lifecycle、acceptance receiptのclosed key集合比較。
- `test_trial_registry.py:3454-3484`
  - launch admission canonical bytes不変。
- 同 `:3949-4176`
  - originless lifecycle start/terminalのexact row。
- `test_autonomous_trial_completeness.py:3325-3379`
  - launch admission closed alternativesとunknown key拒否。
- 新規負例で、originless reportに `campaign_runs` を足してもorigin modeへ昇格しないことを固定。

literal SHAだけには依存せず、既存testどおり非揮発fieldとexact key集合で比較します。

## test配置と影響一覧

| production変更 | 影響する既存test | 新規test配置 |
|---|---|---|
| lifecycle start optional digest | `test_trial_registry.py:3949-4243`、`test_reflux_originless_compatibility.py:515-548,1189-1298` | `test_trial_registry.py` |
| q別identity/envelope順序 | `test_p3_autonomous_workload_trial.py:8175,10280-10323,10712-10925` | 同fileのorigin群末尾 |
| sealed physical entry | `test_p3_s4_loop_trigger_gating.py:906-1001,1164-1238,2614-2743` | 同file |
| provenance v2 / lock ref | `test_reflux_result_evidence.py:81-208` | 同file |
| fixture canonical bytes | `test_reflux_origin_fixture_builder.py:89-225,301-326` | 同file、baseline JSON更新 |
| formal lock/envelope/FC05 | `test_reflux_formal_consumer.py:423-802,961-1011` | 同file |
| origin report/completion | `test_autonomous_trial_completeness.py:1033-1231,2023-2195,2531-3229,4039-5033` | 同file |
| origin material inspection | `test_layer3_report.py:2677-2870` | 同file |
| registry origin acceptance | `test_trial_registry.py:1823-2232,2557-2629,2811-2840` | 同file |
| full originless不変 | `test_reflux_originless_compatibility.py:1176-1298` | 同file。Aだけが所有 |

`test_reflux_origin_topology.py` は既存 topology contractの回帰として使いますが、productionの `reflux_origin_topology.py` は変更しません。

## 変異事前登録候補

単一理由でkillできる候補だけを残します。

| 要件 | 変異点 | 単独で赤にするtest |
|---|---|---|
| 9 | `_derive_origin_campaign_run()` の `query_ordinal` を0固定 | 33identity重複をenvelope前に拒否するtest |
| 10 | capability issuerへ論理 `prepared_campaign` ではなく `cfg_q` を渡す | issuer引数spyと `assert_campaign_binding` 負例 |
| 11 | envelope writeを `begin_attempt_observation` 後へ移動 | call-order test |
| 11 | envelope材料へproducer導出identityでなくcaller値を入れる | caller入力にidentity fieldが無いsignature testと導出一致test |
| 12 | 全qでq0 layoutを再利用 | 33相異root検査 |
| 12 | actual campaign IDをsummaryでなくplanから複写 | wrong-summary-ID負例 |
| 12 | q前の `ensure_remaining()` を削除 | reservation spyの33回検査 |
| 13 | provenance exact key集合から `campaign_run_identity` を外す | v2欠落key resolver負例 |
| 14 | lockから再導出せずprovenance文字列だけを比較 | q10/q11のlock/root/config交換負例。FC05a〜cは通す |
| 14 | ordered WALのlayout所属検査を削除 | 別layout WAL ref負例 |
| 15 | disk readを省きin-memory planだけを検査 | start後disk envelope改変負例 |
| 15 | fixed pathでなくcaller pathを使う | 別pathの同内容envelope負例 |
| 16 | `len(attempts) == len(set(attempts))` を恒真化 | identityは正しいままattempt IDだけ重複する既存FC05a負例 |
| 17 | native `stage/payload` 認識を無効化 | live producer native正例 |
| 17 | mixed family検査でlegacy行を無視 | native + legacy mixed負例 |
| 18 | `campaign_runs` のq順検査を削除 | q8/q9 list順交換負例 |
| 18 | origin branchを常時発火させる | originless full-structure比較 |
| 18 | formal receipt必須を削除 | 33lock/WAL正しいがreceipt欠落のcompletion負例 |

登録しないもの:

- provenance 33値相異だけの変異。
- planned identity全件一致と同じ入力を先取りする重複gate。
- result-evidence exact schemaで先に拒否される後段の同一欠落変異。
- proposal JSONで過剰決定される変異。
- driver-local spyだけがkillし、公開consumerまで到達しない変異。

## 段4で裁定すべき点

1. `campaign_lock_ref` のcarrierを `result-evidence/v2` の第3 refとして新設してよいか。これが無ければ要件14は§Dどおり実装不能です。
2. origin executorがgeneration loop外で使うplanner/auditorの発行契約。特に32 validation maskのmandatory auditor gateを省略してはいけません。
3. 各q直前の `ensure_remaining()` に渡す批准済み保守上限とsafety margin。
4. 第一 waveと第二 waveへ分けるか。分けない場合、A/B/Cは完全並列ではなく A contract -> C -> B -> A acceptance の順になります。
5. `result-evidence/v1` の実在corpus確認。v2新設時に歴史decoderが必要かを決めるためで、確認なしにdecoderは作りません。

## 総括

- 骨子は、slot予約後に33物理identityを導出し、envelopeをlifecycle startへ束縛してから観測を始めることです。
- provenanceはv2だけを受理し、FC03の論理campaign 3項等式を維持します。
- formal consumerはdisk envelope、campaign lock、layout所属WALを現物から再導出します。
- R2 completionは通常Layer3 admissionから分離し、formal receiptと33run再検査を権威にします。
- 最大のリスクは、`campaign_lock` content-addressed refのcarrierが現schemaに存在しないことです。
- executorのauditor入力と1 member時間上限も未確定で、要件12は現状のまま一意実装できません。
- 親は段4で上記5点を裁定し、可能ならcontract waveとexecutor/completion waveへ分けるべきです。
- 編集、test実行、commitは行っていません。