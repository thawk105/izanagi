## 規模の実測

[実測] 調査時の HEAD は `821c7ecfaa0fff6e866d91df637841c1f2a6039c`、worktree は clean である。指定 7 文書を順番どおり全文読了し、pytest は実行していない。

[実測] 親 brief の「50 / 35 / 9 node」は test 関数数だった。`pytest.mark.parametrize` を静的展開すると、`test_attempt_registry_core_s8b_profile.py` は 50 関数 / 78 node、`test_s8b_attempt_registry.py` は 35 関数 / 59 node、`test_attempt_registry_core_equivalence.py` は 9 関数 / 16 node、合計 153 node である。`orchestrator/tests/test_attempt_registry_core_s8b_profile.py:296-2050`, `orchestrator/tests/test_s8b_attempt_registry.py:267-1701`, `orchestrator/tests/test_attempt_registry_core_equivalence.py:436-773`

| 群 | production file と現行 symbol | production 変更量見積もり | test 規模 | 単独整合性 |
|---|---|---:|---:|---|
| [推測] A1 schema / layout | `s8b_attempt_profile.py:22,267-386,418-467` の schema、event key、layout、profile factory。`s8b_attempt_registry.py:451-506,631-763,1051-1106` の path と generation 作成・読出し | 追加 225、変更 80、削除 0、計約 305 行 | 既存回帰 6 node、新設 10〜14 node | v2 を直ちに書込み有効化する形では A2 / A3 / A5 / A6 と不可分。v2 profile を加法的に置くだけなら単独可 |
| [推測] A2 generation / budget / lock seam | `attempt_registry_core.py:986-1129,1363-1399` の budget accumulator と loader。`s8b_attempt_registry.py:509-562,984-1048` の列挙、横断 replay、locked update | 追加 215、変更 120、削除 5、計約 340 行 | 既存回帰 34 node、新設 12〜16 node | core API と lock seam は単独可。adapter 横断 replay は A1 / A3 が必要 |
| [推測] A3 5 軸 slot | `s8b_attempt_profile.py:27-148,272-365,401-408` の slot、codec、series / budget key。`s8b_attempt_registry.py:163-183,766-839` の state、slot lookup、address | 追加 155、変更 55、削除 0、計約 210 行 | legacy symbol を保存すれば既存更新 0、新設 8〜10 node | 明示的な v2 type として加法的に置けば単独可。既存 `S8BAttemptSlot` の置換は admission recovery を壊す |
| [推測] A4 理由語彙 / projection | `s8b_attempt_profile.py:388-399,418-467`、`attempt_registry_core.py:168-175,1081-1119` | 追加 120、変更 35、削除 0、計約 155 行 | 既存回帰 3 node、新設 10〜12 node | derive helper は単独可。非空集合を active profile に入れる変更は A5 の sealed 再導出と不可分 |
| [推測] A5 sealed record / raw bytes | `s8b_attempt_profile.py:333-350`、`attempt_registry_core.py:179-195,891-930,1215-1290,1814-1897`、`s8b_attempt_registry.py:1512-1713` | 追加 180、変更 115、削除 10、計約 305 行 | 既存回帰 29 node、新設 12〜16 node | A1 / A4 が必要。v1 terminal を保存し、v2 専用 API を新設すれば既存 production は維持可能 |
| [推測] A6 capability / claim v3 | `s8b_attempt_registry.py:52-68,163-183,811-967,1109-1205,1289-1593,1765-2071` | 追加 170、変更 125、削除 45、計約 340 行 | 既存回帰 55 node、新設 14〜18 node | B1 に加え A2 の locked seam と A3 の 5 軸が必要。単独不可 |

[推測] 共有 hunk の重複を除いた production 差分は約 1,250〜1,500 changed LOC、新設 test は約 55〜70 node、既存 test の編集は互換 symbol を保存すれば 20 node 未満に抑えられる。ただし回帰確認対象は直接 153 nodeに加え consumer test を含む。現行 3 production file は合計 4,512 行で、変更対象 block だけでも約 1,900 行ある。`attempt_registry_core.py:168-195,986-1399,1814-1897`, `s8b_attempt_profile.py:22-467`, `s8b_attempt_registry.py:315-2071`

[実測] A1 の既存直接回帰 node は `test_genesis_is_create_only_and_rejects_alternate_or_symlinked_paths`、`test_relative_repo_root_is_canonicalized_before_handle_is_issued`、`test_guarded_writer_internal_fault_removes_partial_staging[write|fsync]`、`test_new_registry_directories_fsync_each_parent_entry`、consumer の `test_real_adapter_creates_and_exactly_reuses_complete_genesis` の 6 node である。`test_s8b_attempt_registry.py:1012,1064,1248,1296`, `test_s8b_floor_attempt_launcher.py:510`

[実測] A2 の既存 34 node は、profile 側の `test_s8b_profile_closes_slot_binding_budget_and_reason_policy`、`test_s8b_genesis_accepts_omitted_manifest_fields_and_rejects_undeclared_value`、`test_s8c_genesis_requires_manifest_contract_and_preserves_exact_row[3]`、`test_genesis_rejects_recovery_history_under_a_different_policy_profile[6]`、`test_genesis_rejects_recovery_history_when_enable_flag_changes`、`test_recovery_receipt_rejects_non_string_reason_at_evidence_gate[2]`、`test_recovery_rejects_nested_receipt_change_with_stale_digest`、`test_recovery_rejects_receipt_targeting_a_different_start`、`test_recovery_rejects_replaced_row_start_fence`、`test_recovery_rejects_reason_echo_substitution`、rechained recovery 5 node、`test_recovery_row_rejects_terminal_or_value_field_injection[4]`、`test_recovery_row_rejects_primary_value_injection_at_exact_schema_gate`、`test_known_event_round_trip_passes_and_unknown_event_is_rejected`、`test_profile_only_event_cannot_acquire_terminal_semantics`、`test_s8c_formal_profile_rejects_mismatch_that_compat_replays`、adapter 側の `test_atomic_update_fault_points_leave_only_old_or_new_complete_bytes` と `test_classification_publish_faults_pin_slot_claim_before_exact_retry`、equivalence の `test_unknown_event_rejection_reason_is_identical` である。`test_attempt_registry_core_s8b_profile.py:296,374,511,621,647,934,1028-1095,1270-1478,1871`, `test_s8b_attempt_registry.py:1187,1330`, `test_attempt_registry_core_equivalence.py:473`

[実測] A3 は既存 4 軸 symbol を変更せず `S8BV2AttemptSlot` / `S8BV2SlotCodec` を新設するため、変更 symbol を参照する既存 node は 0。既存 4 軸を直接置換すると profile 62 node、adapter 56 nodeに波及するので採らない。`test_attempt_registry_core_s8b_profile.py:65-219`, `test_s8b_attempt_registry.py:78-240`

[実測] A4 の既存直接回帰は `test_s8b_profile_closes_slot_binding_budget_and_reason_policy`、`test_retryable_terminal_after_observation_hits_only_observation_guard`、`test_s8c_formal_profile_differs_only_by_reason_equality_policy` の 3 node である。`test_attempt_registry_core_s8b_profile.py:296,792,1763`

[実測] A5 の既存 29 node は profile 側の `test_series_order_accepts_first_slot_and_rejects_skip_and_empty_retry_set`、`test_recovery_reason_does_not_bypass_ordinary_terminal_retryable_set`、`test_observation_lifecycle_is_accepted_but_cannot_open_a_later_slot`、`test_retryable_terminal_after_observation_hits_only_observation_guard`、terminal / recovery order 4 node、`test_profile_only_event_cannot_acquire_terminal_semantics`、`test_strict_8b_reason_match_rejects_input_that_8c_still_accepts`、`test_s8c_formal_profile_matching_terminals_keep_compat_bytes[3]`、`test_s8c_formal_profile_rejects_reason_replacement_before_null_matrix[3]`、`test_s8c_formal_profile_rejects_mismatch_that_compat_replays`、`test_s8c_formal_entrypoints_and_producers_are_strictly_routed`、adapter 側の terminal / handle / resume 10 node、equivalence の `test_reference_core_and_facade_event_and_receipt_bytes_are_identical` である。`test_attempt_registry_core_s8b_profile.py:689-792,1170-1297,1478,1709,1801-1952`, `test_s8b_attempt_registry.py:267-461,1064,1135,1330,1701`, `test_attempt_registry_core_equivalence.py:436`

[実測] A6 の既存 55 node は、profile の lifecycle / recovery / formal 23 node、adapter の handle、classification claim、observation、legacy marker、resume、publish 31 node、equivalence 1 nodeである。adapter の実名は `test_terminal_rejects_unclassified_handle_and_accepts_full_order`、`test_handle_registry_rejects_constructor_and_replace_forgery`、`test_terminal_requires_exact_stored_receipt_and_accepts_restored_bytes[2]`、`test_terminal_independently_rejects_changed_cached_receipt_bytes`、`test_slot_classification_claim_allows_exact_retry_and_rejects_new_reason`、failure observation 5 node、`test_observe_rejects_classification_claim_identity_tampering[3]`、`test_observe_rejects_claim_receipt_digest_mismatch`、legacy marker 9 node、`test_relative_repo_root_is_canonicalized_before_handle_is_issued`、resume 2 node、publish 3 node、`test_adapter_preserves_caller_repetition_without_derivation` である。`test_attempt_registry_core_s8b_profile.py:689-1871`, `test_s8b_attempt_registry.py:267-1701`, `test_attempt_registry_core_equivalence.py:436`

## 分割の判定

[実測] (P1-a) の「全 A1〜A6 を 1 wave、実装子 1〜2 本、fix 3 巡以内」は反証する。parametrize 展開後の直接 test 面だけで 153 node、production 見積もりは約 1,250〜1,500 changed LOCであり、前 wave の 600〜850 LOC / 35〜55 node 見積もりを超える。

[推測] 第 1 推奨は次の 1 案に絞る。

| checkpoint | 内容 | 完了時の production 状態 |
|---|---|---|
| [推測] A1'、本 wave | core の seeded budget replay、v1/v2 を別 type・profile・layout にする加法的基盤、5 軸 codec、理由 projection、session serializer、v2 terminal validator、世代列挙、profile resolver、`_atomic_update_locked`。既存 v1 public API は維持し、v2 adapter mutation はまだ開かない | 既存 production は v1 のまま整合。既存 test は変更せず回帰可能。v2 core/profile は単体 test 可能 |
| [推測] A2'、次 wave | v2 generation の create-only publish、横断 budget を使う v2 mutation、B1 capability 消費、sealed terminal API、claim v3、v2 resume | A の全契約が完成。B2 が consume する current-generation reader 境界が確定 |

[実測] A1' は既存 `S8BAttemptSlot`、`S8BSlotCodec`、`S8B_REGISTRY_LAYOUT`、`make_s8b_domain_profile()` を v1 compatibility symbol として保存する。このため `s8b_holdout_admission.py:5363-5622` の legacy recovery reader、`s8b_scheduler_accounting.py:319-350` の 4 軸 reader、launcher の現行 fake / real adapter test を壊さない。

[推測] A1' と A2' の境界は下記 signature で固定できる。A1' 単独では v2 profile を public mutationへ渡すと明示拒否し、未完成 generation を書かない。従って A1' のみを積んだ checkpoint でも production は整合し、既存 test の緑を要求できる構造になる。

[実測] 両 checkpoint とも D1341 により land しない。A1'、A2'、B2、D1、C、D2 を unlanded checkpoint として保持し、配線と proof consumer が揃うまで land 可能とは扱わない。`decisions-verbatim.md:76-95`

## 実装プラン

[推測] A1' で新設・変更する module-level signature は次で固定する。

```python
# attempt_registry_core.py:23-25
BudgetCounts: TypeAlias = dict[Hashable, int]

@dataclass(frozen=True, slots=True)
class TransitionPolicy(Generic[SlotT]):
    require_previous_terminal: bool
    forbid_retry_after_observation: bool
    allow_recovered_abandonment: bool
    max_series_attempts: int | None
    require_terminal_reason_equals_classification: bool
    budget_key: Callable[[SlotT], Hashable] | None
    max_consumptions_per_budget_key: int | None
    retryable_terminal_opens_next_attempt: bool = field(
        default=True, kw_only=True
    )

@dataclass(frozen=True, slots=True)
class DomainProfile(Generic[SlotT, BindingT]):
    schema: SchemaProfile
    layout: RegistryLayout
    statuses: tuple[str, ...]
    retryable_reasons: frozenset[str]
    slot_codec: SlotCodec[SlotT]
    binding_codec: BindingCodec[SlotT, BindingT]
    transition_policy: TransitionPolicy[SlotT]
    recovery_policy: RecoveryPolicy | None = None
    process_identity_keys: frozenset[str] = _DEFAULT_PROCESS_IDENTITY_KEYS
    build_genesis_fields: Callable[
        [str, PurePosixPath, str], Mapping[str, Any]
    ] | None = None
    freeze_id_from_genesis: Callable[[Mapping[str, Any]], str] | None = None
    binding_conflict_message: str = "attempt rows do not share one binding"
    binding_mismatch: Callable[[BindingT, BindingT], str | None] | None = None
    terminal_row_validator: Callable[
        [Mapping[str, Any]], None
    ] | None = field(default=None, kw_only=True)

def _assert_registry_rows_with_budget_counts(
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: DomainProfile[SlotT, BindingT],
    expected_binding: BindingT | None = None,
    initial_started_budget_counts: Mapping[Hashable, int] | None = None,
) -> tuple[RegistryRows, BudgetCounts]

def load_attempt_registry_with_budget_counts(
    data: bytes,
    *,
    profile: DomainProfile[SlotT, BindingT],
    expected_binding: BindingT | None = None,
    initial_started_budget_counts: Mapping[Hashable, int] | None = None,
) -> tuple[RegistryRows, BudgetCounts]

def record_attempt_terminal(
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: DomainProfile[SlotT, BindingT],
    freeze_id: str,
    slot_id: Hashable,
    binding: BindingT,
    terminal_status: str,
    raw_output_sha256: str,
    report_sha256: str | None,
    observation_sha256: str | None,
    primary_value: Any,
    finished_at: str,
    failure_reason: str | None = None,
    sealed_session_record: Mapping[str, Any] | None = None,
) -> RegistryRows
```

[推測] `assert_registry_rows()` と `load_attempt_registry()` の既存 signature と戻り型は不変にし、上記 helper の rows 部分だけを返す wrapper にする。`attempt_registry_core.py:986-990,1391-1399`

[推測] profile 層には既存 v1 symbol を残し、次を新設する。`s8b_attempt_profile.py:22-152,267-467`

```python
S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION = "s8b-floor-attempt-registry/v2"

S8BV2SlotIdentity: TypeAlias = tuple[str, str, int, int, int]
S8BV2SeriesKey: TypeAlias = tuple[str, str, int, int]

@dataclass(frozen=True, slots=True)
class S8BV2AttemptSlot:
    freeze_holdout_key: str
    configuration_id: str
    repetition: int
    measurement_ordinal: int
    attempt_ordinal: int
    schedule_row_sha256: str

@dataclass(frozen=True, slots=True)
class S8BV2SlotCodec:
    exact_keys: ClassVar[frozenset[str]]

    def parse(self, value: object, *, label: str) -> S8BV2AttemptSlot
    def to_json(self, slot: S8BV2AttemptSlot) -> dict[str, Any]
    def slot_id(self, slot: S8BV2AttemptSlot) -> S8BV2SlotIdentity
    def series_key(self, slot: S8BV2AttemptSlot) -> SeriesKey
    def attempt_ordinal(self, slot: S8BV2AttemptSlot) -> int
    def schedule_sha256(self, slot: S8BV2AttemptSlot) -> str

@dataclass(frozen=True, slots=True)
class S8BTerminalProjection:
    terminal_status: str
    failure_reason: str | None
    raw_output_sha256: str
    report_sha256: str
    observation_sha256: str | None
    primary_value: int | float | None

def serialize_session_line(record: Mapping[str, Any]) -> bytes

def derive_s8b_terminal_projection(
    sealed_session_record: Mapping[str, Any],
) -> S8BTerminalProjection

def _s8b_v2_budget_key(slot: S8BV2AttemptSlot) -> S8BBudgetKey
def _assert_s8b_v2_terminal_row(row: Mapping[str, Any]) -> None

def make_s8b_v1_domain_profile(
    *,
    registry_layout: RegistryLayout = S8B_REGISTRY_LAYOUT,
    max_consumptions_per_budget_key: int,
    recovery_authority_id: str,
    recovery_authority_policy_sha256: str,
) -> DomainProfile[S8BAttemptSlot, S8BAttemptBinding]

def make_s8b_v2_domain_profile(
    *,
    max_consumptions_per_budget_key: int,
    recovery_authority_id: str,
    recovery_authority_policy_sha256: str,
) -> DomainProfile[S8BV2AttemptSlot, S8BAttemptBinding]
```

[推測] 新定数は `S8B_V2_SCHEMA_PROFILE`、`S8B_V2_REGISTRY_LAYOUT`、`S8B_SYNTHETIC_V1_REGISTRY_LAYOUT`、`S8B_V2_SLOT_CODEC`、`S8B_V2_RETRYABLE_FAILURE_REASONS` とする。v2 layout は `floor-attempt-registries/{freeze_sha256}/{protocol_sha256}/registry.jsonl`、v2 retryable 集合は承認済み 4 語とする。`s8b_attempt_profile.py:367-402`

[推測] adapter の A1' module-level signature は次で固定する。`s8b_attempt_registry.py:451-506,509-562,984-1048`

```python
def _relative_registry_path(
    *,
    freeze_sha256: str,
    protocol_sha256: str | None = None,
) -> PurePosixPath

def _entry_paths(
    repo_root: Path,
    *,
    freeze_sha256: str,
    protocol_sha256: str | None = None,
    requested_registry_path: Path | None = None,
) -> tuple[Path, Path]

def registry_path(
    repo_root: Path,
    *,
    freeze_sha256: str,
    protocol_sha256: str | None = None,
) -> Path

def _peek_registry_genesis(data: bytes) -> Mapping[str, Any]

def _registry_generation_paths_locked(
    root: Path,
    freeze_sha256: str,
) -> tuple[Path, ...]

def _profile_and_binding_for_generation(
    *,
    path: Path,
    genesis: Mapping[str, Any],
) -> tuple[
    core.DomainProfile[Any, profile8b.S8BAttemptBinding],
    profile8b.S8BAttemptBinding,
]

def _load_other_generation_budget_counts_locked(
    *,
    root: Path,
    current_path: Path,
    freeze_sha256: str,
    current_profile: core.DomainProfile[Any, Any],
) -> core.BudgetCounts

def _run_prelock_snapshot_hook(path: Path) -> None

def _atomic_update_locked(
    lock: admission._AdmissionRootLock,
    *,
    root: Path,
    path: Path,
    profile: core.DomainProfile[Any, Any],
    binding: profile8b.S8BAttemptBinding,
    transition: Callable[
        [core.RegistryRows],
        tuple[core.RegistryRows, TransitionResultT],
    ],
    prepare: Callable[[TransitionResultT, bytes], None] | None = None,
) -> tuple[core.RegistryRows, TransitionResultT]
```

[推測] `_atomic_update()` の既存 signature は変えず、`_run_prelock_snapshot_hook(path)`、`with admission._locked(root) as lock`、`_atomic_update_locked(lock, ...)` の順へ分ける。`s8b_attempt_registry.py:984-1048`

[推測] A1' の core 実装は `assert_registry_rows()` の `started_budget_counts = {}` を seed の検証済み copyへ置換し、各 start で累積し、rows と最終 counts を返す。旧 wrapper は空 seed を渡す。`attempt_registry_core.py:1019,1120-1129,1333`

[推測] A1' の adapter 実装は root lock 内で、current path 以外を protocol 名順に full replayし、同じ counts を current old bytes と candidate bytesの両方へ渡す。candidate のみ上限超過なら `prepare` と staging より前に拒否する。`s8b_attempt_registry.py:1003-1028`

[推測] A1' の generation 列挙は canonical 1 段 `registry.jsonl` と、lowercase 64 hex の real directory 内 `registry.jsonl` だけを返す。64 hex symlink、非 directory、registry 欠落、unsafe file は拒否し、それ以外の sibling は無視する。`s8b_attempt_registry.py:509-562`

[推測] A1' の test 追加位置は profile test の `:296-373,672-853` と adapter test の `:1012-1329,1492-1531` とする。新 node は少なくとも、seeded replay の exact-limit / 11th rejection、v1 canonical / synthetic layout、v2 5 軸、measurement と recovery の分離、4 projection 正例 + observed 正例、projection mismatch、serializer bytes、sibling ignore、hex symlink、不完全 generation、unknown historical policy、hook 1 回、既存 6 return type の保持を含める。

[実測] 変更 symbol の現行呼出しは次が全数である。

- [実測] `TransitionPolicy(...)` は production 2 件、`s8b_attempt_profile.py:447` と `trial_registry.py:2150`。新 field は keyword-only default `True` にして両者を壊さない。

- [実測] `DomainProfile(...)` は production 2 件、`s8b_attempt_profile.py:440` と `trial_registry.py:2113`。`terminal_row_validator` は keyword-only default `None` とする。

- [実測] `load_attempt_registry()` は production 7 件、`s8b_attempt_registry.py:1007,1014,1075,1104,1838`、`s8b_holdout_admission.py:5620`、`s8b_scheduler_accounting.py:335`。test は profile 23 件 `:355,385,553,641,666,956,1045,1069,1089,1112,1291,1318,1338,1364,1382,1413,1448,1458,1472,1514,1522,1884,1889`、adapter 3 件 `:1213,1239,1403`、equivalence 1 件 `:491`。signature は不変。

- [実測] `assert_registry_rows()` の呼出しは core 内 11 件、`attempt_registry_core.py:1386,1547,1593,1665,1751,1762,1811,1823,1895,1908,1970`。signature は不変。

- [実測] core `record_attempt_terminal()` は production 3 件、`trial_registry.py:3363`、`s8b_attempt_registry.py:1650,1700`。test 4 件、`test_attempt_registry_core_s8b_profile.py:161,1608,1689`、`test_attempt_registry_core_equivalence.py:336`。新引数は optional keyword-only とする。

- [実測] adapter `record_attempt_terminal()` は production 1 件 `s8b_floor_attempt_launcher.py:637`、test 2 件 `test_s8b_attempt_registry.py:207,476`。legacy API は不変。

- [実測] `_atomic_update()` は 6 件、`s8b_attempt_registry.py:1183,1439,1556,1666,1716,1756`。戻り値は順に `(rows, (slot, capability))`、`(rows, _ClassificationResult)`、`(rows, str)`、`(rows, None)`、`(rows, None)`、`(rows, None)` のままにする。

- [実測] `registry_path()` は production 0 件、test 2 件 `test_s8b_attempt_registry.py:1040,1052`。`protocol_sha256=None` を legacy 1 段とするため既存 call は不変。

[推測] A2' との境界 signature は次だけを今固定し、実装詳細は次 wave へ送る。

```python
def _publish_registry_generation_create_only(
    *,
    root: Path,
    path: Path,
    payload: bytes,
) -> None

def _atomic_update_with_consumption_marker(
    *,
    root: Path,
    path: Path,
    profile: core.DomainProfile[Any, Any],
    binding: profile8b.S8BAttemptBinding,
    slot: profile8b.S8BV2AttemptSlot,
    marker: admission.FloorAttemptConsumptionMarker,
    measurement_generation_claim_digest: str,
    attempt_id: str,
    campaign_run_id: str,
    manifest_sha256: str,
    run_relpath: str,
    cell_id: str,
    transition: Callable[
        [core.RegistryRows],
        tuple[core.RegistryRows, TransitionResultT],
    ],
    prepare: Callable[[TransitionResultT, bytes], None] | None = None,
) -> tuple[core.RegistryRows, TransitionResultT]

def reserve_attempt_slot(
    repo_root: Path,
    *,
    profile: core.DomainProfile[Any, profile8b.S8BAttemptBinding],
    binding: profile8b.S8BAttemptBinding,
    slot_id: Hashable,
    run_start_receipt_sha256: str,
    process_identity: Mapping[str, Any],
    started_at: str,
    admission_claim_digest: str,
    attempt_id: str,
    campaign_run_id: str,
    manifest_sha256: str,
    run_relpath: str,
    cell_id: str,
    deferred_output_reader: Callable[[], bytes],
    consumption_marker: admission.FloorAttemptConsumptionMarker | None = None,
) -> ReservedAttempt

def record_sealed_attempt_terminal(
    observation: CapturedObservation,
    *,
    sealed_session_record: Mapping[str, Any],
    finished_at: str,
) -> None

def record_sealed_classified_failure_terminal(
    failure: ClassifiedFailure,
    *,
    sealed_session_record: Mapping[str, Any],
    finished_at: str,
) -> None

def resume_attempt(
    repo_root: Path,
    *,
    profile: core.DomainProfile[Any, profile8b.S8BAttemptBinding],
    binding: profile8b.S8BAttemptBinding,
    slot_id: Hashable,
    deferred_output_reader: Callable[[], bytes],
    admission_claim_digest: str | None = None,
    attempt_id: str | None = None,
    campaign_run_id: str | None = None,
    manifest_sha256: str | None = None,
    run_relpath: str | None = None,
    cell_id: str | None = None,
    consumption_marker: admission.FloorAttemptConsumptionMarker | None = None,
) -> ReservedAttempt | ClassifiedAttempt | ClassifiedFailure | CapturedObservation

def _slot_address_payload_v3(
    *,
    binding: profile8b.S8BAttemptBinding,
    slot: profile8b.S8BV2AttemptSlot,
) -> dict[str, Any]

def _assert_legacy_consumed_marker(
    root: Path,
    *,
    state: _AttemptState,
    slot: profile8b.S8BAttemptSlot,
) -> Mapping[str, Any]
```

[実測] `reserve_attempt_slot()` の現行 adapter caller は production 1 件 `s8b_floor_attempt_launcher.py:454`、test helper 1 件 `test_s8b_attempt_registry.py:140`。`consumption_marker=None` は v1 だけで受理し、v2 では拒否する。

[実測] `resume_attempt()` の現行 caller は test 4 件 `test_s8b_attempt_registry.py:1096,1124,1162,1393`。全て v1 のため optional default で維持する。

[推測] 受理集合の方向は次のとおりとする。

| 項目 | 方向 | 承認 |
|---|---|---|
| [推測] 明示的 v2 profile、2 段 path、5 軸 slot | 広がる | plan v2 と段 4 A2-2 / B2-6 で承認済み |
| [推測] canonical 1 段 v1 の既存 API | 不変 | legacy compatibility |
| [推測] sibling 非 generation entry の無視 | 広がる | 親 P1-d と前 wave A-5 で承認済み |
| [推測] 横断 budget seed | 狭まる | D1193 / D1340 で承認済み |
| [推測] v2 の 4 retryable reason を raw core が受ける面 | 広がる | plan v2 で承認済み。ただし sealed projection validator と同時にだけ active 化する |
| [推測] v2 terminal の sealed record 再導出 | 狭まる | 段 4 A2-5 / B2-4 / B2-5 で承認済み |
| [推測] v2 claim v3 の full binding | 狭まる | plan v2 A6 と段 4 で承認済み |
| [推測] v1 claim v2 と legacy marker | 不変 | 既存回復経路の保存 |

[推測] A1' で新設する拒否の署名と正例は次のとおりとする。

- [推測] `initial_started_budget_counts` の値が bool、負数、非 intなら `AttemptRegistryCoreError("[attempt-slot-order] initial budget count is invalid")`。正例は `{("holdout-a", "configuration-a"): 9}` と 1 startで 10。

- [推測] seed と rows の合計が cap を超えれば `AttemptRegistryCoreError("[attempt-slot-order] attempt consumption exceeds the profile budget")`。正例は合計 10 ちょうど。

- [推測] v2 `measurement_ordinal` または `attempt_ordinal` が bool / 負数なら `AttemptRegistryCoreError("[attempt-registry-schema] ... is not a nonnegative integer")`。正例は planned `(repetition=0, measurement_ordinal=0, attempt_ordinal=0)`。

- [推測] v2 terminal の `valid` が exact boolでない、または `valid=True` と `excluded_reason!=None` が同居すれば `AttemptRegistryCoreError("[s8b-terminal-projection] sealed session validity differs")`。正例は `valid=True, excluded_reason=None, session_median=100.0`。

- [推測] invalid session の理由が 4 語外なら `AttemptRegistryCoreError("[s8b-terminal-projection] excluded_reason is outside the closed set")`。正例は `excluded_reason="performance_anomaly"` から `sealed-measurement-dispersion`。

- [推測] terminal row と導出 projection の status / reason / digest / primary value が 1 fieldでも違えば `AttemptRegistryCoreError("[attempt-terminal] sealed session projection differs: <field>")`。正例は全 field を `derive_s8b_terminal_projection()` から設定した row。

- [推測] session record に NaN / Infinity / 非 JSON 値があれば `AttemptRegistryCoreError("[s8b-terminal-projection] sealed session record is not JSON")`。正例は有限数だけを持つ session。

- [推測] generation 名が 64 lowercase hexだが symlink、非 directory、または内部 `registry.jsonl` 欠落なら `S8BAttemptRegistryError("[s8b-attempt-registry-storage] generation directory is unsafe or incomplete")`。正例は real directory と no-follow regular `registry.jsonl`。

- [推測] generation genesis の path 上 protocol と `protocol_sha256` が違えば `S8BAttemptRegistryError("[s8b-attempt-registry-path] generation protocol differs from genesis")`。正例は directory 名と genesis binding が同値。

- [推測] schema / layout / recovery-policy の組合せを既知 profile へ解決できなければ `S8BAttemptRegistryError("[s8b-attempt-registry-profile] generation profile is not reconstructible")`。正例は現行 scheduler authorityで作った canonical v1 または v2。

## 設計点の決着

[実測] **P1-b は採用するが、外部 lock 直結経路は作らない。** `_locked()` は毎回新しい fd を `os.open()` し、その fdへ blocking `flock(LOCK_EX)` を掛ける。同一 stack の二度目は最初の fd が lock を保持したまま待つため進行不能になる。B1 自身も non-reentrant と明記している。`s8b_holdout_admission.py:699-726,341-344`

[実測] `FloorAttemptConsumptionMarker.use()` の `lock` と `action` が受ける型は同じ opaque `_AdmissionRootLock` である。生存条件は exact type、private seal、`_active is True`、exact root、exact int fd、`fstat(fd)` が regular fileであること。context exit で `_active=False`、unlock、closeされる。`s8b_holdout_admission.py:289-300,322-368,5115-5137,5219-5227`

[推測] 正しい順序は、呼び手が lock 外で `validate_floor_attempt_consumption_marker(admission, attempt_id=...)` を実行して capability を発行し、その後 adapter を呼ぶ。adapter は prelock snapshot hookを実行し、root lockを一度だけ取り、`marker.use(lock=lock, ..., action=lambda active_lock: _atomic_update_locked(active_lock, ...))` とする。validator 自身が lockを取るため、発行を `_atomic_update_locked` 内で行ってはならない。`s8b_holdout_admission.py:5082-5103`

[実測] `_PRELOCK_SNAPSHOT_HOOK` は現行 `:997-1002` で authoritative lock より前に走る rendezvous である。`_atomic_update_locked()` へ移してはならない。`_run_prelock_snapshot_hook(path)` を outer wrapper と marker wrapperの両方が lock 前に 1 回だけ呼ぶことで意味を保存する。`s8b_attempt_registry.py:984-1004`

[実測] 既存 `_atomic_update` 6 callerの戻り型と例外変換は現在 wrapper 側で加工されていない。inner helper も例外を catchしないため、core / adapter / admission exceptionの型と messageをそのまま維持できる。`s8b_attempt_registry.py:1183,1439,1556,1666,1716,1756`

[推測] `_assert_consumed_marker` の `:1539` は v2 では `_atomic_update_with_consumption_marker()` に置換する。`:2042` は既存 resume lock 内で `marker.use(..., action=resume_validation)` とする。v1 だけは名前を `_assert_legacy_consumed_marker()` に変えて raw validator を保存する。`s8b_attempt_registry.py:1458-1509,1521-1562,1835-2052`

[実測] B1 capability の第 4 軸は journal の planned=0 / retry=`retry_ordinal` であり、v2 registry の recovery `attempt_ordinal` ではない。従って `marker.use()` へは `repetition=slot.repetition`、`attempt_ordinal=slot.measurement_ordinal` を渡す。v2 `slot.attempt_ordinal` は 0 のときだけ consumption capability を使える。`s8b_holdout_admission.py:4961-5001`

[実測] **P1-c は一部反証する。** 3 種の受理表は次になる。

| 種類 | 読めるか | 書けるか | budget に数えるか | 拒否条件 |
|---|---|---|---|---|
| [推測] 正規 1 段 v1 | yes、legacy profileで full replay | yes、既存 v1 APIだけ | yes | v1 schema / 4軸 / 1段 root / known recovery policyから外れれば拒否 |
| [実測] 合成 2 段 v1 | 条件付き。列挙はするが、trusted profileを再構成できる場合だけ | no | full replayできた場合だけ yes | live 現物は unknown historical policyのため拒否 |
| [推測] v2 | yes、v2 profileで full replay | yes、A2' の安全な generation publish後 | yes | 5軸、sealed terminal、v3 claim、known authorityのいずれか不一致で拒否 |

[実測] live 合成 v1 genesis は `recovery_policy_sha256=c7c753...` だが、現行 scheduler authorityから導出される digest は `6ac1b69...` で一致しない。genesis は authority id / policy digestの元値を持たず、193 行は freeze 1 + start 96 + seal 96で recovery receiptも無い。従って genesis peekだけから trusted `DomainProfile` を再構成できない。`.../d388477f.../registry.jsonl:1`, `s8b_scheduler_accounting.py:40-48,65-102`, `attempt_registry_core.py:209-230,715-725`

[推測] 合成 v1 を通すために recovery-policy digest比較を省く案、または sibling catalogを trust rootにする案は採らない。前者は受理面を緩め、後者は廃止済み合成 fileを新しい production authorityへ昇格させる。

[実測] **P1-d は採用する。** `consumption-catalog.jsonl` の literal を読む tracked production consumer は 0 件である。世代 authority は 64 hex real directory 内の `registry.jsonl` だけなので、非 64 hex sibling fileを無視しても registry rowやbudget startが不可視になることはない。`s8b_attempt_profile.py:378-386`, repo-wide `rg` 実測

[推測] `consumption-catalog.jsonl` は列挙対象にも profile reconstructionにも使わない。64 hex名の fileやsymlinkは「sibling」として無視せず、generation authorityを偽装しているため拒否する。

[実測] **A4 の非空集合は raw core の受理集合を広げる。** `_assert_null_matrix()` の `retryable-failure` 分岐は reason が `retryable_reasons` に含まれることを要求するため、現行空集合では全 reason が必ず拒否される。genesis でも profile集合との完全一致を要求する。`attempt_registry_core.py:689-701,933-964`, `s8b_attempt_profile.py:395,444`

[実測] 空集合が現在恒真に作用する場所は、profile test の pin `:302,802` と、retryable terminal null matrixである。`test_attempt_registry_core_s8b_profile.py:296-357,792-829`

[推測] 4 語の active 化は raw coreだけでは広がるが、v2 profile の `terminal_row_validator` が sealed recordから理由を再導出し、caller理由を受けないため、adapter全体では「4つの承認済み状態だけを受ける閉集合」になる。`retryable_terminal_opens_next_attempt=False` とし、measurement failureが recovery ordinalを開かないようにする。

[実測] **A5 の現行 2 byte列は異なる。** core canonical JSONは空白なし・newlineなしで、例は `b'{"event":"session","valid":true}'`。journal writerは標準 separatorの空白とnewlineを持ち、例は `b'{"event": "session", "valid": true}\\n'`。`attempt_registry_core.py:197-202`, `s8b_floor_campaign.py:1593-1604`

[推測] 単一源は journal の既存 durable bytes側へ寄せる。`serialize_session_line()` は `json.dumps(..., ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"` とし、A1' では profile helper、C では `_journal_append()` と terminal builderの双方が使う。

[推測] v1 terminal は sealed objectを持たないため、既存 `raw_output_sha256` を再計算せず従来どおり読む。v2だけ `sha256(serialize_session_line(sealed_session_record))` と row fieldを照合する。既存 durable bytesの移行・再書込みは不要である。

[実測] **A6 の現行 claim addressは freeze + 4軸、payloadはそれに schedule-rowとclassification / admission fieldsを足した形で、protocol / schedule bindingが欠ける。** `s8b_attempt_registry.py:811-901`

[推測] claim v3 の addressとpayloadへ `protocol_sha256`、`schedule_sha256`、`measurement_ordinal` を追加する。既存 `freeze_sha256` と合わせて full binding 3値、既存4軸のうち recovery `attempt_ordinal` を残して5軸になる。

[推測] v3 create-only pathは v3 addressの canonical digestから導出する。同じ freeze / configuration / repetitionでも protocol、schedule、measurement ordinal、recovery ordinalのいずれかが違えば別 pathになる。

[推測] 既存 claim fileは読めなくならない。v1 registryは旧 v2 claim schemaと旧 addressを使い、v2 registryだけv3へ dispatchする。v3 readerがv2 fileを誤受理する経路は作らない。

## 未解決・親へ返す点

[実測] live 合成 2 段 v1 を「必ず読める」とする P1-c は、trusted recovery profileを genesisから再構成できないため成立しない。本 plan は fail-closed rejectionを採る。これを受理対象へ戻すなら、`campaign-fixture-recovery-authority` と policy digestを production trust rootへ加える明示裁定が必要である。

[実測] `consumption-catalog.jsonl` にはその fixture authorityが記録されているが、tracked consumerは 0 であり、合成残骸から新 authorityを採用する根拠にはならない。既存 bytesは読んだだけで変更していない。

[推測] A2' 以後も B1 capability は recovery `attempt_ordinal` を証明しない。A の境界は「measurement consumptionは registry `attempt_ordinal=0` のみ」と固定する。verified recovery側で ordinal 1 以後を発行する仕組みは本閉包の後半であり、ここでは作らない。

[実測] `marker.use()` の docstringが明記する journal TOCTOU窓は本 planでも閉じない。閉じた保証を test名やコメントへ書いてはならない。`s8b_holdout_admission.py:339-348`

[実測] sandboxは read-onlyであり、pytest、collection、mutation、green確認は実行していない。node数は AST と decorator列の静的計数である。

[実測] A1' と後続 A2' はいずれも D1341 の unlanded checkpointである。段9でlandせず、B2 / D1 / C / D2の片側を先行landする前提も置いていない。

## 総括

- [実測] 単位 A 全体は約 1,250〜1,500 changed LOC、直接 test 153 nodeの閉包で、1 wave案を反証する。
- [推測] 第1推奨は A1'=加法的 core/profile/read-only adapter基盤、A2'=v2 mutation/capability/claim有効化の2分割。
- [推測] A1' は既存 v1 symbolと挙動を保存するため、単独 checkpointでも production整合と既存 test緑を要求できる。
- [実測] P1-b は採用するが、prelock hookを外殻に残し、capabilityはlock取得前に発行する。
- [実測] P1-c は一部反証し、live合成2段v1はunknown recovery policyのためfail-closedとする。
- [実測] P1-d は採用し、consumer 0の `consumption-catalog.jsonl` は世代列挙から無視する。
- [実測] A4の非空理由集合はraw coreを広げるため、sealed projection validatorと同時にだけ有効化する。
- [推測] A1' / A2' ともlandせず、6段閉包完成後の1 commitだけをland対象とする。