## 総括

1. **共通 core:** 状態遷移・canonical row 構築・replay 検証だけを `attempt_registry_core.py` へ移す。8c 固有 slot codec、P/C binding、Git history、既定 path、receipt storage、公開 capability は `trial_registry.py` に残す。

2. **facade:** C03 が要求する 6 attempt API は `trial_registry.py` 内の実 `def` として残す。`assert_trial_registry_acceptance()` 本体も動かさず、C02/C03/C08/C09/C10 の直接呼出し・文字列・到達性を維持する。

3. **8b adapter:** `shared_admission_root()` 配下を master とする原則は妥当。ただし `_locked()` は再入不能で、同じ lock は直列化しか保証せず複数 file の crash atomicity や全履歴唯一性を保証しない。lock-aware 内部 API、WAL/recovery、versioned binding が必要。

4. **出力前分類:** 現行 `measure_fn` は起動・待機・parse を一体化しているため、`pre_observation_reason` を足すだけでは不足する。opaque launch と output parse の二相 API に分け、retry は create-only receipt だけから認可する。

5. **再抽選バイアス:** 「最初に terminal へ到達した attempt」は一般には偏る。post-observation crash は attempt 0 を欠測として主値に固定し、次 slot は診断用に限定するか、同一 attempt の checkpoint continuation にしなければならない。

6. **テスト:** 8c は facade 所有者・C01–C12 の `(id,status,reason)`・event/receipt bytes・例外理由を golden 化する。8b は全 crash cut、同一反復限定、closed reason、global retry cap、主値不変を状態機械テストにする。pytest は実走していない。

7. **分割:** A/B は file 上は概ね分離するが、8b が必要とする recovery/selection policy が core API を変えるため、そのままの完全並列は危険。core/profile API を先に固定してから B を開始する二段分割が正しい。

親 provisional 裁定:

- **P1: 修正付き採用。** 新 module と profile 注入は採るが、8c の Git/path/storage まで共通 core に入れない。
- **P2: 原案のままでは不採用。** 同じ lock は使うが、非再入性・cross-file crash cut・全履歴欠如への対策を追加して初めて成立する。
- **P3: 原案のままでは不採用。** 二層化の概念は採るが、monolithic `measure_fn` と output-derived retry trigger を残す限り抜け道がある。
- **P4: 不採用。** completion-conditioned selection なので informative censoring により偏り得る。
- **P5: 不採用。** 8b に `campaign_id` はなく `campaign_run_id` であり、これを slot key に入れると freeze-wide identity を分断する。

## 1. 共通 core の境界

### `trial_registry.py:1818-3431` の全 symbol

凡例:

- **core+wrapper:** 実装本体を core へ移すが、互換性のため同名の薄い `def` を 8c 側に残す。
- **8c adapter/store:** ドメインまたは保存方式に固有なので本体を残す。
- **facade:** 公開 signature を保った実 `def` とし、core を呼ぶ。
- **alias:** 現状の代入を維持する。

| 現行行 | symbol | 配置 |
|---:|---|---|
| 1818 | `_attempt_digest` | core+wrapper |
| 1826 | `_attempt_text` | core+wrapper |
| 1832 | `_attempt_process_identity` | core+wrapper。exact keys は profile 注入 |
| 1859 | `_attempt_slot_config` | 8c slot codec。`trial_id/arm/holdout/campaign_id/replicate_index` 固有 |
| 1869 | `_parse_attempt_slot` | 8c slot codec。`ARMS/HOLDOUTS/_TRIAL_ID_RE` 固有 |
| 1909 | `_assert_attempt_slot_layout` | core+wrapper。series key/ordinal を codec 経由にする |
| 1928 | `_attempt_schema_version` | core+wrapper。schema profile 注入 |
| 1938 | `_assert_attempt_v2_chain` | core+wrapper |
| 1969 | `_parse_attempt_genesis` | core+wrapper。path/reasons/slot parser は profile 注入 |
| 2036 | `_attempt_capability_payload` | 8c binding adapter。P/C と 8c slot field 固有 |
| 2060 | `_attempt_capability_digest` | core hash 本体 + 8c payload wrapper |
| 2081 | `_parse_attempt_row` | core+wrapper。event key set/binding codec/status を注入 |
| 2225 | `_assert_attempt_null_matrix` | core+wrapper |
| 2283 | `_assert_attempt_registry_rows` | core replay 本体。receipt lookup は store 経由 |
| 2598 | `_load_attempt_registry_bytes` | core+wrapper |
| 2616 | `_attempt_registry_target` | 8c store。canonical repo-relative path 固有 |
| 2634 | `_write_create_only` | 8c store primitive。8b は既存 `_write_exclusive()` を使う |
| 2672 | `create_attempt_registry_genesis` | 実 facade。core の `build_genesis()` と 8c store を呼ぶ |
| 2729 | `_attempt_tree_paths` | 8c Git store |
| 2758 | `_looks_like_attempt_genesis` | 8c Git history scanner |
| 2778 | `_assert_attempt_registry_history_append_only` | 8c Git store/history |
| 2840 | `load_attempt_registry` | 実 facade。history 検査後に core replay |
| 2886 | `_locked_attempt_registry_update` | 8c store。registry file 自身への `flock` |
| 2948 | `_assert_attempt_capability` | 8c adapter。型・seal・P/C 公開契約固有 |
| 2984 | `reserve_attempt_slot` | 実 facade。8c capability を現行 field のまま生成 |
| 3107 | `record_attempt_start` | alias のまま残す |
| 3110 | `_attempt_receipt_payload` | core builder + 8c capability wrapper |
| 3134 | `classify_attempt` | 実 facade。固定 receipt dir への書込は 8c store |
| 3244 | `classify_attempt_failure` | alias のまま残す |
| 3247 | `begin_attempt_observation` | 実 facade |
| 3314 | `record_attempt_terminal` | 実 facade |

この範囲内に新規 dataclass 定義はなく、定数相当は 3107/3244 の alias だけである。

### 範囲外だが core 抽出に関係する symbol

- `trial_registry.py:57-65` の既定 path/schema、`:101-167` の status・retry reason・exact key 集合は、I2/C03 のため8c側に残す。
- `AttemptSlotCapability` (`:371-404`) と `_ATTEMPT_SLOT_CAPABILITY_SEAL` (`:99`) は8c側に残す。field 追加・型置換もしない。
- `_ATTEMPT_ZERO_SHA256` (`:476`) と `_attempt_event_sha256`、`_attempt_v2_event_row`、`_attempt_v2_previous_hash`、`_attempt_pre_observation_seal_payload` (`:479-532`) は core 本体へ移し、必要なら同名 wrapper を残す。
- `_canonical_json_bytes` (`:463-473`)、JSON decoder、Git/path helpers、`TrialRegistryError/_fail` は8c全体でも使用されるため残し、core service として注入する。
- `assert_attempt_registry_acceptance` (`:3432-3555`) は8c固有 acceptance なので移さない。

### 注入型

```python
SlotT = TypeVar("SlotT")
BindingT = TypeVar("BindingT")
SeriesKey = tuple[Hashable, ...]

class SlotCodec(Protocol[SlotT]):
    exact_keys: frozenset[str]

    def parse(self, value: object, *, label: str) -> SlotT: ...
    def to_json(self, slot: SlotT) -> dict[str, JsonValue]: ...
    def slot_id(self, slot: SlotT) -> str: ...
    def series_key(self, slot: SlotT) -> SeriesKey: ...
    def attempt_ordinal(self, slot: SlotT) -> int: ...
    def schedule_sha256(self, slot: SlotT) -> str: ...

class BindingCodec(Protocol[BindingT]):
    event_keys: frozenset[str]

    def parse(self, row: Mapping[str, object], *, label: str) -> BindingT: ...
    def to_event_fields(self, binding: BindingT) -> dict[str, JsonValue]: ...
    def identity(self, binding: BindingT) -> Hashable: ...
    def capability_payload(
        self, *, slot: SlotT, binding: BindingT, freeze_id: str
    ) -> dict[str, JsonValue]: ...

@dataclass(frozen=True, slots=True)
class SchemaProfile:
    current: str
    readable: frozenset[str]
    genesis_keys: Mapping[str, frozenset[str]]
    event_keys: Mapping[str, Mapping[str, frozenset[str]]]

@dataclass(frozen=True, slots=True)
class RegistryLayout:
    registry_path: PurePosixPath
    classification_receipt_dir: PurePosixPath

@dataclass(frozen=True, slots=True)
class TransitionPolicy:
    require_previous_terminal: bool
    forbid_retry_after_observation: bool
    allow_recovered_abandonment: bool
    max_series_attempts: int | None

@dataclass(frozen=True, slots=True)
class AttemptDomainProfile(Generic[SlotT, BindingT]):
    schema: SchemaProfile
    layout: RegistryLayout
    statuses: tuple[str, ...]
    retryable_reasons: frozenset[str]
    slot_codec: SlotCodec[SlotT]
    binding_codec: BindingCodec[BindingT]
    transition_policy: TransitionPolicy

class AttemptStore(Protocol):
    def read_verified(self) -> bytes: ...
    def create_genesis(self, payload: bytes) -> Path: ...
    def atomic_update(
        self,
        transition: Callable[[tuple[dict[str, JsonValue], ...]], TransitionResult],
    ) -> object: ...
    def create_receipt(self, digest: str, payload: bytes) -> Path: ...
    def read_receipt(self, digest: str) -> bytes: ...
```

8c の束縛は次の形にする。

```python
@dataclass(frozen=True, slots=True)
class S8CSlot:
    slot_id: str
    trial_id: str
    arm: str
    holdout: str
    campaign_id: str
    replicate_index: int
    attempt_index: int
    schedule_row_sha256: str

@dataclass(frozen=True, slots=True)
class S8CBinding:
    prereg_content_commit: str
    prereg_effective_commit: str
```

- `trial_id`: `S8CSlotCodec` が `_TRIAL_ID_RE` を注入して検証。
- `arm/holdout`: 同 codec が `ARMS/HOLDOUTS` を注入。
- prereg commit: `S8CBindingCodec` が full commit、P/C 一致、capability payload を担当。
- schema/version: `SchemaProfile` に v1/v2 と全 exact-key 集合を注入。
- 既定 path/receipt dir: `RegistryLayout` に現行文字列をそのまま注入。
- retryable reason: `ATTEMPT_RETRYABLE_FAILURE_REASONS` を `frozenset` のまま注入。
- 8c policy は `require_previous_terminal=True`、`forbid_retry_after_observation=True` とし、現行 `trial_registry.py:2361-2383` を変えない。

## 2. facade と C01–C12 probe

具体形は「import した core 関数の再 export」ではなく、以下である。

```python
def reserve_attempt_slot(
    *,
    repository_root: Path,
    freeze_id: str,
    slot_id: str,
    prereg_content_commit: str,
    prereg_effective_commit: str,
    run_start_receipt_sha256: str,
    process_identity: Mapping[str, Any],
    started_at: str,
    registry_path: Path = DEFAULT_ATTEMPT_REGISTRY_PATH,
) -> AttemptSlotCapability:
    return _S8C_ATTEMPT_ADAPTER.reserve_attempt_slot(
        repository_root=repository_root,
        freeze_id=freeze_id,
        slot_id=slot_id,
        prereg_content_commit=prereg_content_commit,
        prereg_effective_commit=prereg_effective_commit,
        run_start_receipt_sha256=run_start_receipt_sha256,
        process_identity=process_identity,
        started_at=started_at,
        registry_path=registry_path,
    )
```

同形で `create_attempt_registry_genesis`、`load_attempt_registry`、`classify_attempt`、`begin_attempt_observation`、`record_attempt_terminal` を残す。公開 signature、default、return type、例外型を変えない。

`_functions()` は同名 `def` が後から再束縛されても除外する (`s8c_preregistration_evidence.py:835-846`)。したがって、実 `def` の後に同名 import/assignment を置いても不可である。

### 各 probe が `trial_registry.py` に要求するもの

| probe | `trial_registry.py` への要求 |
|---|---|
| C01 | 直接要求なし。`p3_autonomous_workload_trial.py` の workload/ratified-freeze 到達性だけ。 |
| C02 | `bind_trial_arm`→`assert_issued_trial_binding`,`resolve_arm_input`; `assert_issued_trial_arm_execution`→issued binding/input; `assert_rederived_trial_arm_execution`→issued assertion/`bind_trial_arm`; `_expected_registered_arm_execution_record`→`resolve_arm_input`; `assert_trial_registry_acceptance` 内の直接 live call 3件。さらに3 digest field と文字列 `"arm_execution"`。`s8c_preregistration_evidence.py:1967-2027`。 |
| C03 | 下記の関数存在、関数内構造、producer/acceptance 到達性、top-level 定数、field 文字列。`:1613-1778`。 |
| C04 | `forbid_trial_restart` が実 `def` として存在し、workload `main→run_trial` から到達すること。`:2055-2079`。 |
| C05 | 直接要求なし。 |
| C06 | 直接要求なし。 |
| C07 | 直接要求なし。 |
| C08 | `assert_effective_commit_exact_parent`、`load_effective_binding_at_commit`、`validate_preregistration_binding`、`_blob_at_commit`、`_assert_ancestor`、`admit_registered_launch`、`load_launch_binding`、`_derive_launch_binding`、`assert_trial_registry_acceptance` の実 `def` と、P/C/H の実引数データフロー・admission/acceptance からの到達性。`:1781-1930`。 |
| C09 | `assert_trial_registry_acceptance` が直接 `assert_campaign_layer3_chain` を呼び、live 文字列 `"no-build"` と `"certifying"` を持つ。`:2194-2219`。 |
| C10 | `assert_trial_registry_acceptance` が直接 `verify_s8c_cross_binding` を呼ぶ。`:2240-2262`。 |
| C11 | 直接要求なし。 |
| C12 | 直接要求なし。 |

C03 の全要求は次のとおり。

- 実 `FunctionDef` が必要な13関数 (`:1624-1639`):
  `load_trial_manifest`,
  `load_effective_binding_at_commit`,
  `validate_preregistration_binding`,
  `_find_registration_for_manifest`,
  `_assert_manifest_registry_trial_set`,
  `_assert_runtime_report_trial_set`,
  `_assert_runtime_report_cells`,
  `load_attempt_registry`,
  `reserve_attempt_slot`,
  `create_attempt_registry_genesis`,
  `classify_attempt`,
  `begin_attempt_observation`,
  `record_attempt_terminal`。
- acceptance 自体は `assert_trial_registry_acceptance` または `accept_trial` の実 `def` (`:1603-1610`)。
- `_trial_canonical_tuple` の live node に `trial_id/arm/holdout/campaign_id/generations` 属性 (`:1649-1661`)。
- `_assert_manifest_registry_trial_set` から `_trial_canonical_tuple` を2回以上呼び、`set/len` を使う (`:1662-1671`)。
- `_assert_runtime_report_cells` に live 文字列 `cells/workload/workload_flags/ycsb_rratio/campaign_id` と `get` 呼出し (`:1672-1684`)。
- acceptance に `legacy` 名を条件にした早期 return がない (`:1685-1690`)。
- acceptance から同じ `trial_registry.py` 所有者の8関数へ declared-call 到達性 (`:1692-1713`)。特に `load_attempt_registry` facade を飛ばして core だけを呼ぶと I4 を破る。
- producer `run_trial` から `_reserve_registered_attempt_slot` が到達可能 (`:1715-1730`)。
- producer から `trial_registry.py` 所有者の `reserve_attempt_slot/classify_attempt/begin_attempt_observation/record_attempt_terminal` が到達可能 (`:1731-1746`)。
- top-level 名として `MANIFEST_SCHEMA_VERSION`、`REGISTRATION_SCHEMA_VERSION`、`DEFAULT_ATTEMPT_REGISTRY_PATH`、`ATTEMPT_REGISTRY_SCHEMA_VERSION`、`ATTEMPT_STATUSES`、`ATTEMPT_RETRYABLE_FAILURE_REASONS` (`:1748-1760`)。
- module 全体の属性/文字列集合に `manifest_sha256/prereg_content_commit/prereg_effective_commit/trials/cells` (`:1761-1773`)。

したがって facade 化で壊れ得るのは C03 だけではない。`assert_trial_registry_acceptance` 全体を core wrapper にすると C02、C09、C10 の直接呼出し/文字列が落ち、C08 の到達性も落ちる。現行本体 `trial_registry.py:5349-5901` はそのまま残し、`:5769-5776`→`assert_attempt_registry_acceptance` (`:3432`)→`load_attempt_registry` (`:3451`) の経路を維持する。

## 3. 8b adapter

### slot と事前割当

8b slot は次で固定する。

```python
@dataclass(frozen=True, slots=True)
class FloorAttemptSlot:
    slot_id: str
    freeze_holdout_key: str
    configuration_id: str
    repetition: int       # s8b_floor_campaign の round
    attempt_ordinal: int  # 0=planned, 1..N=rescue
    schedule_row_sha256: str
```

`repetition` は inner `reps` ではなく schedule の `round` である。現行 schedule は各 round に各 cell が1回現れる (`s8b_floor_campaign.py:1499-1505`)。

現行 `retry_slots_per_cell` は反復ごとでなく cell 全体の上限である (`s8b_holdout_admission.py:1264-1295`, `s8b_floor_campaign.py:5114-5126`)。したがって以下を genesis に両方封印する。

- 全 `(holdout, configuration, round, attempt_ordinal=0..R)` の潜在 slot。
- `max_rescue_consumptions_per_cell=R` の global cap。

これをせず各 round に R 回を許すと、凍結済み protocol の retry budget を `n_sessions` 倍にしてしまう。

事前割当は、manifest が create-only で封印された `s8b_floor_campaign.py:6612-6621` より後、`runner.run()` (`:6880-6882`) より前に行う。具体的には `_reserve_floor_holdout_observations_core()` の既存 lock 節 `s8b_holdout_admission.py:1323-1435` 内で、全 cell claim と同じ transaction に genesis の create/verify を入れる。

既に同一 freeze の `attempt-ledger.jsonl` に consumption があるのに genesis がない場合、後付け割当は拒否する。過去の exploratory run を正式 registry へ昇格させてはならない。

### root と ledger の束縛

推奨配置:

- master root: `shared_admission_root(repo_root)` (`s8b_holdout_admission.py:427-444`)。
- binding: `floor-attempt-registry-bindings/<freeze_sha256>.json`
- registry: `floor-attempt-registries/<freeze_sha256>/registry.jsonl`
- receipts: `floor-attempt-registry-receipts/<sha256>.json`
- lock: 既存 `ledger.lock` だけ。独立 lock は作らない。

binding は最低限、canonical relative path、genesis bytes hash、freeze/protocol/schedule hash、profile/schema hash、closed reason set を持つ。claim digest 群も genesis に入れ、既存 admission authority と結ぶ。

`attempt-ledger.jsonl` の既存 v1 row (`s8b_holdout_admission.py:3865-3869`) は変更しない。新しい consumption row は v2 とし、`slot_id/start_event_sha256/registry_genesis_sha256/transaction_id` を追加する。inspector `:4493-4524` は schema ごとの exact-key 集合を分け、既存 v1 bytes をそのまま受理する。

### `_locked()` の判定

`_locked()` は呼出しごとに新しい FD を `os.open()` し (`:505-513`)、その FD に `LOCK_EX` を取る (`:514-519`)。depth、thread-local、既存 FD 再利用はない。別 open file description に対する nested `flock` は同一 process でも既存 lock と競合し得るため、**再入可能ではない**。

したがって次の形に変える。

```python
with _locked(root) as transaction:
    floor_attempt_registry.reserve_locked(transaction, ...)
    _write_consumed_marker_locked(...)
    _append_attempt_ledger_locked(...)
```

- adapter の `_locked` 版は lock を取得しない。
- public entrypoint がちょうど一度だけ既存 lock を取得する。
- 現行 `consume_attempt_ticket()` (`:3796-3841`) から nested adapter 呼出しをしない。
- journal authorization 検査 `:3746-3793` も decide/write の同じ lock 節へ移す。

同じ lock は競合する writer を直列化するが、registry、marker、ledger の三 file を crash-atomic にはしない。transaction intent/commit row と deterministic recovery を追加し、各 write 後の crash cut を replay できるようにする必要がある。

さらに、既存 admission は削除・同一 bytes 再構成を検出できないと明記している (`s8b_holdout_admission.py:8-11`, `:4054-4058`)。従って P2 だけでは §10.5 の「全履歴で第二 root を拒否」を満たさない。正式 gate を開くには、genesis hash/canonical path を Git の content commit に pin するか、同等の append-only authority が必要である。それが用意されるまで実装は formal execution を fail-closed に保つ。

### 消費範囲

次 slot の認可条件は core replay だけから導出する。

- series key が同じ `(freeze_holdout_key, configuration_id, repetition)`。
- ordinal は直前の次だけ。skip 禁止。
- cell 全体の rescue 消費が global cap 未満。
- observed primary、correctness/parse/nonfinite terminal、成功済み反復からは次 slot 不可。
- `s8b_floor_campaign.py:5155-5169` の「`valid is False` なら retry」は廃止。
- `_retry_round()` (`:5381-5391`) は registry の `retry_authorized` series だけを列挙する。
- `_assert_attempt_authorized_by_journal()` (`s8b_holdout_admission.py:3782-3792`) の output-derived `valid is False` 条件は、classification receipt hash と registry transition の検証へ置換する。

## 4. 出力前分類の実装点

### 現在 `measure_fn` より前に確定できる証拠

`_Runner._run_session()` で実際に確定済みなのは次である。

- reservation recheck の成否 (`s8b_floor_campaign.py:5210-5213`)。
- seq/round/cell/kind/retry ordinal/trigger/attempt ID と fsync 済み session-start (`:5213-5219`)。
- freeze/protocol/manifest hash と frozen cell coordinates (`:5052-5074`, `:5221-5223`)。
- binary の build hash と実測直前 hash (`:5224-5233`)。
- pre-probe の raw 結果と競合判定 (`:5235-5248`)。
- admission/ticket consumption は現在 wrapper 内 (`:4993-5014`) なので、外側の `measure_fn` 呼出し前には確定していない。

現行 API で `measure_fn` 後に得られるもの:

- callback が例外を送出したか (`:5251-5259`)。
- post-probe (`:5261`)。
- `ScalePoint` の throughput、exec failure、rep evidence、run command (`:5263-5288`)。
- CV/median/partial/performance reason (`:5290-5303`)。

ただし `measure_fn` 自身が `ScalePoint` を作るために既に性能出力を読んでいる。従って、外側で `scale_point` の属性へまだ触っていないことは「出力を読む前」の証明にならない。

### 必要な二相化

`_wrap_admission_aware_measure()` (`:4962-5016`) と default measure (`:6790-6817`) を次へ分割する。

```text
reserve slot + session-start
  -> launch_and_wait()       # raw output は opaque
  -> strict post-probe
  -> classify external facts
  -> create-only classification receipt
  -> retryable: terminalize without parsing
     or
     begin_observation()
       -> parse_output()
       -> report-only excluded_reason
       -> terminal
```

新しい receipt に封印するもの:

- genesis/slot/start event hash、claim digest、session-start digest。
- process identity、binary hash、command hash。
- pre/post probe raw digestと競合 bit。
- spawn errno、wait status、signal、scheduler event、timeout authority。
- authority/policy digest、classified timestamp。
- exact reason または `null`。
- `performance_output_read: false`。
- raw output の path/hashは分類時には読まない。content hash は receipt 後の terminal に記録する。

8b の retryable closed set は新 schema で次へ固定することを推奨する。

```python
FLOOR_RETRYABLE_PRE_OUTPUT_REASONS = frozenset({
    "competing_process",
    "scheduler_preempted",
    "scheduler_wall_timeout",
    "node_failure",
    "launcher_spawn_failure",
})
```

単なる nonzero exit、任意の `RuntimeError`、parser error、correctness-red は retryable にしない。現行 `"launch_failure"` は `exec_failures` や callback 例外を広くまとめているため (`:5308-5316`)、report-only reason として残す。

`"nonfinite_or_partial_output"` (`:307`, `:5317-5321`) と `assess_session()` が返す performance reason は常に report-only とする。

### P3 に残る穴

二層 field を足すだけでは、以下が残る。

- `measure_fn` が parse 後に例外を選べる。
- `RuntimeError` が launcher failure と parser/correctness failure を区別しない。
- post-probe より前に default `measure_point()` が出力を読んでいる。
- `_round_failed_cells()` が `valid` を見て retry を発火する。
- admission 側も failed session の `valid is False` を retry authority にしている。
- 同一 process が raw path を直接読めるなら `performance_output_read:false` は自己申告にすぎない。
- classification receipt 作成前の crash を安全に再分類するには、parser capability がまだ発行されていなかったことを recovery state から証明する必要がある。

従って編集点は `:5254-5322` だけでなく、`:4962-5016`, `:5155-5174`, `:5210-5391`, `:5528-5788`, `:6177-6225`, `:6790-6817` と `s8b_holdout_admission.py:3746-3841` に及ぶ。

## 5. 再抽選バイアス

P4 は一般には偏る。

潜在性能値を \(Y\)、attempt が terminal へ到達する事象を \(C\) とすると、最初の terminal 値が従うのは目標分布 \(P(Y)\) ではなく \(P(Y\mid C=1)\) である。timeout は遅い値ほど発生しやすく、負荷や温度は node failure と性能の両方へ影響し得る。値を人間が直接選ばなくても、完了事象で条件付けた時点で informative censoring になる。

安全な代案は次の順である。

1. attempt ordinal 0 を観測前に主 attempt と固定する。
2. observation-start 後に terminal がなければ、その反復の主値は欠測・判定不能とする。
3. 次 slot は診断・運用復旧用として全件報告するが、主値へ昇格させない。
4. 技術的に可能なら、次 slot を新しい draw にせず、同一 attempt の checkpoint continuation として残りの predeclared rep を継続する。
5. terminal 到達値への置換をどうしても採る場合は、estimand を「固定 timeout と外部障害条件の下で完了した run の条件付き性能」へ変更しなければならず、元の床値と同一とは主張できない。

pre-observation で性能 bytes が存在しない失敗は、closed external reason に限って次 slot を主値候補にできる。post-observation crash と同じ扱いにはしない。

## 6. テスト計画

### 新規 core tests

`orchestrator/tests/test_attempt_registry_core.py:new:1`

- 8c profile で現行 v1/v2 genesis/start/seal/classification/observation/terminal の canonical bytes と event hash を golden 比較。
- exact-key、null matrix、chain tamper/reorder、slot skip、duplicate terminal、P/C mismatch の現行 gate/message 比較。
- 8c policy が observation-start 後の retry を拒否すること。
- 8b profile が同一 series だけを進め、global cell cap を守ること。
- profile を変えても core に `trial_id/ARMS/HOLDOUTS/prereg_commit/output/s8c-*` の literal がない AST 検査。

### 8c facade tests

`orchestrator/tests/test_trial_registry.py` では、少なくとも次の symbol 群が影響面になる。

- `AttemptSlotCapability`
- `_load_attempt_registry_bytes`
- `_assert_attempt_registry_rows`
- `create_attempt_registry_genesis`
- `load_attempt_registry`
- `reserve_attempt_slot` / `record_attempt_start`
- `classify_attempt` / `classify_attempt_failure`
- `begin_attempt_observation`
- `record_attempt_terminal`
- history/alternate-root/receipt/null-matrix tests

互換 wrapper を残すため、既存テスト変更は原則ゼロを目標にする。公開 signature、dataclass fields、alias identity、例外文字列を追加 tripwire にする。

ただし、この file は単独段の必読射影に含まれていないため、規律上読んでいない。従って「60参照」の正確な test 関数名と現行行番号だけは本 plan では確定不能である。author/review dispatch では `test_trial_registry.py` を必読射影へ追加し、編集前に全60 call site を AST で列挙する必要がある。

### C01–C12 tests

`test_s8c_preregistration_predicates.py` で直接影響を受ける current-tree tripwire:

- `test_current_repository_snapshot_has_zero_satisfied_predicates` (`:187-195`)
- `test_current_repository_snapshot_exactly_matches_head` (`:198-204`)
- `test_current_repository_gap_reason_snapshot_requires_cross_wave_review` (`:207-249`)
- `test_contract_declares_exact_terminal_definition_path_universe` (`:467-477`)

C03 の facade/reachability 防壁:

- `test_c03_negative_control_rejects_manifest_cell_check_removal` (`:2883-2901`)
- `test_c03_negative_control_rejects_deterministic_false_strict_branch` (`:2925-2961`)
- `test_c03_producer_reachability_requires_classification_and_terminal` (`:2964-2995`)
- `test_c03_acceptance_legacy_bypass_is_unsatisfied` (`:3034-3057`)
- `test_c03_acceptance_requires_independent_runtime_cell_route` (`:3060-3081`)
- `test_c03_noop_helpers_do_not_prove_manifest_registry` (`:3084-3111`)

追加する test:

- six facade を import re-export に置換した fixture が C03 UNSATISFIED になること。
- six facade が実 `FunctionDef` で、同名 rebinding がないこと。
- `assert_trial_registry_acceptance` から `trial_registry.py` 所有の `load_attempt_registry` への graph edge。
- C02/C09/C10 の直接 call と live string が抽出前と同じこと。
- 全 C01–C12 の `(id, status, reason_code)` が `:219-248` と一致すること。evidence SHA は source 変更で当然変わるため同値対象に含めない。

### 8b state-machine tests

`orchestrator/tests/test_s8b_floor_attempt_registry.py:new:1`

- manifest seal 後・runner 前の全 slot 事前割当。
- genesis 後の slot/reason/schema 追加拒否。
- 同一 `(holdout,config,round)` の next ordinal だけ消費。
- 他 cell/他 round、skip、observed済み、correctness terminal、枯渇後を拒否。
- global `retry_slots_per_cell` cap。
- pre-probe competing は output parser 未呼出しで retryable receipt。
- parser/nonfinite/CV/exec-failure-derived reason は retry 不可。
- observation-start 後 crash は主値欠測、後続 attempt は診断専用。
- registry/marker/attempt-ledger の各 write 後 crash と recovery。
-同一 slot を並行消費して一方だけ成功。
- `_locked()` の nested acquisition を使わないこと。
- v1 attempt-ledger/claim bytes を変更せず mixed-version inspection ができること。
- binding/genesis/receipt/raw hash/process identity の一対一束縛。
- 全 started attempt が terminal の有無を含め result projection に現れること。

既存 output bytes は、親検査で基準 commit との `git diff -- output/s8b-freeze output/s8c-trial-registry output/s8c-preregistration` を確認する。ここでは pytest もその比較も実走しておらず、緑は主張しない。

## 7. 分割の可否

親の A/B は同一 file を直接編集する可能性は低いが、semantic conflict がある。

- A が現行8cだけを見て core を作ると、`trial_registry.py:2361-2383` 相当の「previous terminal 必須・observation 後 retry 禁止」を core に固定しやすい。
- B は post-observation recovery、diagnostic slot、global cell cap、lock-aware store を追加するため、結局 A 所有の core/profile API を変更する。
- B の分類 receipt/event schema も core の replay model に影響する。

正しい分割は次である。

1. **A0、先行:** core の `SlotCodec/BindingCodec/AttemptStore/TransitionPolicy` と 8c/8b 両 profile の型契約を固定する。
2. **A:** pure core 抽出、8c facade、8c golden/C01–C12 tests。
3. **B:** 固定済み API 上で 8b adapter、shared-root transaction/recovery、二相 launcher、primary projection を実装する。
4. A/B 統合後に 8c bytes/reason と8b crash-cutをまとめて受理検査する。

A0 を置かず同時編集するなら、`attempt_registry_core.py` が実質的な競合面になるため、親の「編集面は分離」は成立しない。