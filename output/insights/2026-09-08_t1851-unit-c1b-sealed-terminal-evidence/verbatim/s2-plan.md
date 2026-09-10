## 単位 1 の plan

所有 file は次の 2 本だけとする。

- `orchestrator/campaign/s8b_terminal_evidence.py:new`
- `orchestrator/tests/test_s8b_terminal_evidence.py:new`

単位 1 を先に実装・検査し、leaf の API と canonical bytes を固定してから単位 2 / 3 を開始する。

新設 leaf の公開 surface は次に固定する。

```python
@dataclass(frozen=True, slots=True)
class TerminalEvidenceProjection:
    terminal_status: str
    failure_reason: str | None
    measurement_retry_reason: str | None
    campaign_excluded_reason: str | None
    primary_value: float | None
    raw_output_sha256: str
    report_sha256: str
    observation_sha256: str | None
    finished_at: str


@dataclass(frozen=True, slots=True, init=False)
class SealedTerminalEvidenceDraft:
    @property
    def canonical_bytes(self) -> bytes: ...
    @property
    def document(self) -> Mapping[str, Any]: ...
    @property
    def projection(self) -> TerminalEvidenceProjection: ...


@dataclass(frozen=True, slots=True, init=False)
class ValidatedTerminalEvidence:
    @property
    def canonical_bytes(self) -> bytes: ...
    @property
    def document(self) -> Mapping[str, Any]: ...
    @property
    def projection(self) -> TerminalEvidenceProjection: ...
    @property
    def sha256(self) -> str: ...


def derive_terminal_projection(
    *,
    probe_before: Mapping[str, object],
    probe_after: Mapping[str, object] | None,
    failure: Mapping[str, object] | None,
    launch_failures_count: int,
    throughputs: Sequence[float],
    nonfinite_count: int,
    reps_expected: int,
    exec_failures: int,
    rep_integrity_failures: int | None,
    session_cv_max: str,
) -> TerminalEvidenceProjection: ...


def seal_terminal_evidence(
    reservation: object,
    opened: object,
    terminal: object,
) -> SealedTerminalEvidenceDraft: ...


def require_sealed_terminal_evidence(
    value: object,
) -> ValidatedTerminalEvidence: ...
```

内部実装は次の配置にする。

- `new:1-90`: schema、exact key 集合、E2 の 4 語、campaign 語を定義する。schema は literal `s8b-floor-terminal-evidence/v2`。
- `new:91-180`: 上記 3 型。draft / validated capability の唯一の実データは immutable canonical bytes とし、`document` と `projection` はアクセスごとに bytes から再生成する。
- `new:181-360`: strict JSON、duplicate key、exact type/key、SHA-256、probe summary、failure summary、12-key `attempt_binding`、6-key `slot` の検査。
- `attempt_binding` は `freeze_sha256`、`protocol_sha256`、`schedule_sha256`、`slot`、`attempt_id`、`campaign_run_id`、`manifest_sha256`、`run_relpath`、`cell_id`、`classification_receipt_sha256`、`classification_event_sha256`、`observation_event_sha256`。3 個目は契約 1.3 どおり現物の綴りにする。
- `new:361-500`: full `campaign_record` の exact 30 key を検査した後、証拠文書には identity 13 field と計測 11 fieldだけを平文 projection として残す。`workload`、`run_cmd`、`notes`、`probe_before`、`probe_after`、`rep_observations` はそれぞれ named digest に変換し、full record 自体は `campaign_record_sha256` で束縛する。
- `new:501-620`: 私有 sink を `s8b_floor_stats._derive_rep_integrity()`（現物 `s8b_floor_stats.py:471-589`）へ通し、qualified throughput から非有限値を除去して `nonfinite_count` を算出する。`assess_session()` には有限列と元の `reps_expected` を渡す（`s8b_floor_stats.py:127-165`）。
- `new:621-720`: E1 を `if/elif` の順序で実装する。競合、failure/full exec、partial exec かつ assessed reason null、integrity + partial、partial、performance、observed の順とし、辞書変換や `observed` fallback は置かない。
- `new:721-850`: reservation / opened / terminal の全件照合、相互整合、raw line・report・observation digest の再導出。どの不一致も `TerminalEvidenceError("[s8b-terminal-evidence] ...")` とし、状態を変えて救済しない。
- canonical bytes は `attempt_registry_core.canonical_json_bytes()` と同形の compact JSON・LF 無し。`raw_output_sha256` と `report_sha256` は、現行 `serialize_session_line()` の spaced/sorted UTF-8 JSON + LF（`s8b_attempt_profile.py:566-578`）から独立に再計算する。
- `expected_use_perf` の機械導出は launcher の既存 gate `s8b_floor_attempt_launcher.py:565-588` を正本として保持する。leaf に `use_perf_from_receipt()` の新しい直接 call は増やさず、launcher-issued snapshot と receipt digest を照合する。

単位 1 の test は、exact schema、canonical bytes、全 digest、30-key trust root、非有限値、E1 全枝、相互整合、immutable bytes、constructor/replace 攻撃を純関数レベルで閉じる。30-key 集合は `s8b_ratified_freeze._JOURNAL_KEYS["session"]`（`s8b_ratified_freeze.py:262-269`）との集合等値も検査する。

## 単位 2 の plan

所有 file は次の 4 本。

- `orchestrator/campaign/s8b_floor_attempt_launcher.py`
- `orchestrator/campaign/s8b_attempt_profile.py`
- `orchestrator/tests/test_s8b_floor_attempt_launcher.py`
- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py`

### launcher

変更アンカーは次のとおり。

- `s8b_floor_attempt_launcher.py:61-81` `FloorAttemptReservation`
- `:92-104` `FloorMeasurementCapture`
- `:125-138` `OpenedFloorAttempt`
- `:141-157` `FloorAttemptTerminal`
- `:508-598` `_checked_reservation_policy`
- `:618-644` `_reserve`
- `:723-852` `_launch_floor_attempt`
- `:855-876` `launch_floor_attempt`
- `:879-909` `_launch_floor_attempt_for_test`

変更内容:

- `FloorAttemptReservation` に、terminal builder が選べない campaign identity snapshot を加える。対象は `event`、`kind`、`seq`、`round`、`retry_ordinal`、`trigger`、`holdout_id`、`configuration_id`。既存の `attempt_id`、`cell_id`、measurement の `records` / `threads` と合わせて 1.5 の identity 13 field を再構成する。`retry` は `kind == "retry"` から導出する。
- launcher が measurement 前後の時刻、measurement binary digest、capture kwargs snapshot、opened `ScalePoint` surface、私有 rep sink を保持し、証拠の計測 field と比較できるようにする。`duration_s` と `finished_at` を terminal builder の選択値にしない。
- `FloorAttemptTerminal` の既存 status / digest / primary / `finished_at` は比較用 self-report と位置付ける。row へ渡す値は draft の再導出 projection だけとする。
- `_checked_reservation_policy()` の `:521-528` にある v2 一律拒否を外す。ただし `(v2 schema) ⇔ (consumption_marker 非 null)`、protocol digest、mode、receipt/use_perf、reps の検査は genesis/reserve より前に行う。
- `_launch_floor_attempt()` を「共通 prepare」と「schema 別 finalization」に分ける。順序は以下で固定する。

```text
policy 検査
→ genesis
→ reserve
→ probe_before
→ capture / probe_after
→ durable classification
→ token.open()
→ private sink snapshot
→ terminal_builder
→ seal_terminal_evidence()
→ raw output seal
→ observation-start
→ v1: record_attempt_terminal()
→ v2: record_sealed_attempt_terminal(observation, draft)
```

- `:830-851` の現行 terminal call を上記分岐へ置換する。v1 は現在の adapter API と引数をそのまま使う。
- production wrapper `launch_floor_attempt()` だけが固定 adapter の `record_sealed_attempt_terminal()` を呼ぶ。launcher は `ValidatedTerminalEvidence` や core capabilityを受け取らない。
- `_launch_floor_attempt_for_test()` は同じ prepare 本体を通せるが、fake registry が受け取れるのは draft までとする。fake `_Observation` から adapter の validated capability は発行できないことを test する。
- `_CERTIFIED_MEASUREMENT_KEYWORDS`（`:40-54`）、`_owned_post_probe()` の argv / timeout / subprocess site（`:278-307`）は変更しない。

### profile

変更アンカー:

- `s8b_attempt_profile.py:403-477` v1 event keys
- `:490-504` v2 event keys
- `:532-537` retryable reasons
- `:556-563` v2 terminal rejection hook
- `:587-636` v1 profile
- `:639-684` v2 profile

変更内容:

- `_S8B_EVENT_KEYS` は一切変更しない。v1 terminal は現行 exact 24 key のまま。
- `_S8B_V2_EVENT_KEYS` を event 別に組み立て、全 event へ `measurement_ordinal`、terminal だけへ `terminal_evidence_sha256` と `measurement_retry_reason` を加える。v2 terminal は v1 との差集合が exact 3 keyになる。
- `S8B_V2_RETRYABLE_FAILURE_REASONS` を E2 の exact 4 語にする。`S8B_RETRYABLE_FAILURE_REASONS` は空のまま。
- canonical v2 profile の通常 `terminal_row_validator` は capability 無しの core 直呼びを拒否する。adapter が durable evidence を読んだ場合だけ、`_require_sealed_s8b_v2_terminal(row, validated_evidence)` を閉じ込めた private validating profile を使う。
- `_require_sealed_s8b_v2_terminal()` は `type(evidence) is ValidatedTerminalEvidence` を要求し、row の status、両 reason、primary、raw/report/observation digest、classification echo、terminal evidence digestを projection と全件等値にする。
- `make_s8b_v2_domain_profile()` は `retryable_reason_field="measurement_retry_reason"`。v1 factory と s8c 利用者は既定 `"failure_reason"` のまま。

## 単位 3 の plan

所有 file は次の 4 本。

- `orchestrator/campaign/attempt_registry_core.py`
- `orchestrator/campaign/s8b_attempt_registry.py`
- `orchestrator/tests/test_attempt_registry_core_equivalence.py`
- `orchestrator/tests/test_s8b_attempt_registry.py`

### core

変更アンカー:

- `attempt_registry_core.py:198-216` `DomainProfile`
- `:858-1047` `_parse_row`
- `:1050-1100` `_assert_null_matrix`
- `:1361-1438` terminal replay
- `:1484-1585` public replay/load APIs
- `:2000-2083` `record_attempt_terminal`

変更内容:

- `DomainProfile` に keyword-only fieldを加える。

```python
retryable_reason_field: str = field(
    default="failure_reason",
    kw_only=True,
)
```

- `_parse_row()` は expected terminal keys に存在する場合だけ `terminal_evidence_sha256` を non-null digest、`measurement_retry_reason` を nullable text として検査する。
- `_assert_null_matrix()` の署名を次へ変える。

```python
def _assert_null_matrix(
    row: Mapping[str, Any],
    *,
    retryable_reasons: frozenset[str],
    retryable_reason_field: str,
    label: str,
) -> None: ...
```

- retryable / terminal-failure の語彙照合先だけを `retryable_reason_field` へ切り替える。`failure_reason` と classification の等値検査 `:1419-1425` は変更しない。
- `observed` と `not-consumed` では、profile が選んだ reason field も null であることを必須にする。既存の `[attempt-null-matrix] ... observed null matrix differs` / `... not-consumed null matrix differs` を維持する。
- `record_attempt_terminal()` に keyword-only引数を足す。

```python
measurement_retry_reason: str | None = None
terminal_evidence_sha256: str | None = None
```

- `:2070-2075` の `terminal_keys` seam と同じ方式で、key が schema の terminal 集合に含まれる場合だけ row へ emit する。v1 へ非 null値を渡した場合は拒否し、黙って捨てない。
- `assert_registry_rows()`、既存 2 loader、reserve/classify/observe/recovery の各 public signatureへ capability 引数は足さない。

### adapter

変更アンカー:

- `s8b_attempt_registry.py:42-90` token/fault constants
- `:164-316` `_AttemptState` と handle 検査
- `:319-486` profile exact comparator
- `:857-982` current v2 replay
- `:1059-1076` canonical document
- `:1118-1250` durable directory / guarded create-only
- `:1430-1437` receipt path
- `:1575-1606` durable measurement-generation claim
- `:1623-1705` generation replay / atomic validation
- `:1666-1736` `_atomic_update_locked`
- `:1862-1885` public read
- `:1888-2056` reserve
- `:2379-2483` observation and raw digest
- `:2510-2603` observation/legacy terminal
- `:2706-3122` resume

追加する私有境界:

```python
def _terminal_evidence_path(root: Path, digest: str) -> Path: ...

def _validated_terminal_evidence_from_bytes(
    data: bytes,
    *,
    expected_digest: str,
    expected_binding: Mapping[str, Any],
) -> ValidatedTerminalEvidence: ...

def _load_terminal_evidence_locked(
    root: Path,
    registry_bytes: bytes,
    *,
    expected_binding: S8BAttemptBinding,
) -> Mapping[str, ValidatedTerminalEvidence]: ...

def _terminal_validating_profile(
    profile: DomainProfile[Any, Any],
    evidence_by_digest: Mapping[str, ValidatedTerminalEvidence],
) -> DomainProfile[Any, Any]: ...

def record_sealed_attempt_terminal(
    observation: CapturedObservation,
    evidence: SealedTerminalEvidenceDraft,
) -> None: ...
```

実装内容:

- evidence path は `floor-attempt-registry-receipts/terminal-evidence/<digest>.json`。
- root lock 下で registry bytes から terminal digest を抽出し、各 file を no-follow regular fileとして読む。filename、bytes digest、strict JSON、exact keys、canonical bytes、attempt bindingを検査する。
- adapter の private issuer が exact `CapturedObservation` を `_require_handle()`（`:280-316`）へ通し、state の `classification_receipt_sha256`、`classification_event_sha256`、`observation_event_sha256` を draft に補って validated capabilityを発行する。
- capability の normal constructorは閉じる。発行表には canonical bytes digest と identity fingerprintだけを保存し、表 membership 自体は権威にしない。
- `_AttemptState` へ `mode` は足さない。`mode` は既存 measurement-generation claimの canonical documentから読み、現行 claim validator `s8b_holdout_admission.py:985-1051` と durable `mode` field `:1703-1728` を利用して evidence と照合する。
- `_assert_exact_profile()`（`:372-433`）へ `retryable_reason_field` の exact比較を足す。外部から渡された evidence-bound profileは受理せず、canonical profileの検査後に adapter 内だけで validating profileを作る。
- terminal を含み得る replay 8 箇所（`:974`、`:1647`、`:1687`、`:1698`、`:1883`、`:1942`、`:2439`、`:2791`）を adapter 内の中央 evidence-aware loaderへ束ねる。capabilityを core の8 surfaceへ伝播しない。
- `_atomic_update_locked()` は既存 terminal の evidence 集合と今回追加する pending evidenceを合わせた validating profileで old/candidateを検査する。adapter 内の transition callbackにはその profileを渡し、core の既存 APIを呼ぶ。
- terminal candidate の memory validation後、`prepare()` で evidenceを `allow_exact_retry=True` により先に公開し、その後 `:1716-1733` の registry stagingへ進む。
- file-only / row無し crash は許容。rowあり/file無しは次回の中央 replayで拒否する。
- 旧 `record_attempt_terminal()` と `record_classified_failure_terminal()` の v2拒否 `:2536-2541` は残す。新 APIだけが v2 terminalを記録できる。
- `_assert_observation_row()` の slot annotationは v1/v2 unionへ広げるが、exact handle・slot・event digest照合は緩めない。

## 契約 v3 条項と実装の対応表

| 契約 | 実装箇所 |
|---|---|
| 0 | leaf の全件再導出、adapter の sealed-only terminal API。床値 verifierや campaign算出は変更しない |
| 1 | leaf canonical bytes/digest、profile/core の terminal 2 field、adapter evidence path/create-only |
| 1.1 | leaf の平文 projection + named digest。adapter `prepare()` は既存 holdout-safe writerを通す |
| 1.2 | launcher `:508-598` の protocol/mode/perf/reps gate、leaf の全件比較、adapter の durable claim照合 |
| 1.3 | adapter `_AttemptState` `:181-184` の exact 3 digest。`observation_event_sha256` の綴りを採る |
| 1.4 | leaf の finite-only normalization、`_derive_rep_integrity()`、`assess_session(..., reps=reps_expected)` |
| 1.5 | leaf exact 30-key検査と identity/measurement/digest 群の分離 |
| 2 | leaf cross-field validator。全不一致を `[s8b-terminal-evidence]` で拒否 |
| 3 | leaf は `exec_failures == campaign_record.exec_failures` だけを束縛。runner/campaignは変更しない |
| 4 | leaf `derive_terminal_projection()`。campaign `s8b_floor_campaign.py:6242-6254,6296-6327` と同順 |
| 5.1 | core `DomainProfile.retryable_reason_field`、profile v2 `"measurement_retry_reason"` |
| 5.2 | profile E2 exact set、leaf E1、core null matrix、adapter sealed writer |
| 5.3 | core `_assert_null_matrix()` の observed / not-consumed null追加 |
| 5.4 | profile v2 terminal event分岐、core conditional emit |
| 6.1 | launcher draft、adapter exact observationから validated capability発行 |
| 6.2 | launcher test seam、adapter private issuer、strict capability type |
| 6.3 | leaf immutable canonical bytes、adapter digest/fingerprint table |
| 6.4 | leaf/adapter docstring と threat-boundary test。範囲外の同一-process改変に対する防壁は実装しない |
| 7 | adapter central locked replay、nofollow reader、evidence-first publication |
| 8 | 実装なし。claim v4、`_AttemptState.mode`、core 8 surfaceへの capability伝播を入れない |
| 9 | production caller 0 を静的 testで固定し、実環境値域を主張しない。C2/D2は範囲外 |

実装を持たない条項は 6.4 の範囲外宣言、8 の非採用、9 の限界だけであり、いずれも意図的である。逆に、上記 production変更で契約条項を持たないものはない。

## test 設計

### 契約 5.2 の 5 形

次の parametrized positiveを新設する。

```python
def test_contract_5_2_accepts_each_terminal_shape(
    shape: str,
    valid_case: TerminalCase,
) -> None: ...
```

| 形 | 受理する組 |
|---|---|
| 観測前・競合 | `failure_reason="competing_process"`、`measurement_retry_reason="measurement_environment_conflict"`、retryable |
| 観測前・起動失敗 | `failure_reason="launch_failure"`、`measurement_retry_reason="measurement_execution_unavailable"`、retryable |
| 観測後・標本不足 | `failure_reason=None`、`measurement_retry_reason="measurement_sample_incomplete"`、retryable |
| 観測後・分散超過 | `failure_reason=None`、`measurement_retry_reason="measurement_dispersion_exceeded"`、retryable |
| 観測成功 | 両 reason null、observed、primary = assessed median |

各 positive に対し、他 fieldを固定して reason/statusの1箇所だけを変える rejectionを置く。

```python
def test_contract_5_2_rejects_each_nearby_reason_or_status_mutation(
    shape: str,
    mutation: str,
    valid_case: TerminalCase,
) -> None: ...
```

- classification echo改変は `^\[attempt-classification\] terminal .* differs`
- E1と異なる measurement reason、status、primary、digest は `^\[s8b-terminal-evidence\]`
- E2外の語/nullは `^\[attempt-null-matrix\] .* retryable-failure null matrix differs$`

拒否 testは必ず同じ fixtureの無変異 positiveを先に受理させ、冗長な前段 gateの赤を数えない。

### 契約 5.3 の 2 穴

```python
def test_observed_rejects_nonnull_measurement_retry_reason_and_accepts_null(
    valid_observed_rows: RegistryRows,
) -> None: ...
```

拒否署名:

```text
^[attempt-null-matrix] attempt registry line N observed null matrix differs$
```

positive controlは 5.2 の観測成功行。

```python
def test_not_consumed_rejects_nonnull_measurement_retry_reason_without_closing_retryable(
    valid_competing_rows: RegistryRows,
) -> None: ...
```

拒否署名:

```text
^[attempt-null-matrix] attempt registry line N not-consumed null matrix differs$
```

positive controlは 5.2 の観測前・競合 retryable行で、同じ非 null reasonがretryable枝では正当に通ることを示す。

### その他の主要 test

- leaf: exact/missing/extra key、duplicate JSON key、LF混入、NaN/Inf、digest 1-bit変更、12-key binding、30-key campaign record、finite-only列、E1 precedence。
- leaf: holdout-safeな最終 bytesは受理し、`workload` または `run_cmd` の平文を戻した変異は既存 scannerに拒否される。
- launcher: v1旧APIとv2 sealed APIの分岐、classified→open→draft→observation→terminal順序、finished clock、raw bytes、fake registryが validated capabilityを得ないこと。
- core/profile: v1 exact keys不変、v2差集合 exact 3、E2 exact 4、reason fieldのkeyword-only/default、capability無し v2直呼び拒否。
- adapter: genuine v2の5形、old API拒否、constructor/replace/fake handle拒否、mode/protocol/3 digestの別 attempt swap拒否。
- durability: evidence-first crash、exact retry、rowあり/file無し、filename/digest mismatch、noncanonical file、symlink/FIFO、別attempt evidence swap、file-only/row無し許容。
- replay: terminal後のread、別slot reserve、cross-generation budget、atomic old/candidate、observation snapshot、resume、prefix capture/inspectの各面でevidenceを再読させる。

## 既存 test への影響

対象既存 test file は4本、現状合計175 test関数である。既存期待値を意味的に変えるのは2箇所に限定する。

- `test_s8b_floor_attempt_launcher.py:892-914`  
  「v2は全副作用前に拒否」から、「v2はdraftまで進めるがfake registryはproduction capabilityを発行できない」へ期待を変更する。v1 test 22関数の期待値は変えない。
- `test_attempt_registry_core_s8b_profile.py:2174-2218`  
  v2 retryable集合を空からE2 exact 4語へ、terminal key差集合を1 keyから3 keyへ更新する。

既存 nodeへの追加 assertion:

- `test_attempt_registry_core_s8b_profile.py:296-357`: v1 retryable集合、reason field既定、v1 exact terminal keysを固定。
- `:762-790`: v1 observed lifecycleの受理。
- `:721-742`: recovery reasonがv1 terminal retryable集合を迂回しないこと。
- `:2221-2250`: `retryable_reason_field` がkeyword-only・既定 `"failure_reason"`、v2だけ別fieldであること。
- `:2253-2382`: v1同理由受理、異理由拒否、validator前のgate順序を維持し、v2部分だけsealed経路へ書き換える。
- `:2385-2429`: v1の retryable-next-attempt policy既定を維持。
- `test_attempt_registry_core_equivalence.py:447-483`: generic core抽出前後のevent/receipt bytes一致を維持。
- `:690-753`: s8c facadeの公開signatureが変わらないこと。
- `test_s8b_attempt_registry.py:427-498`: v1 full lifecycleとhandle forgery拒否。
- `:621-657`: v1 pre-output failureでもactual output digestを使う。
- `:1939-1993`: v1 pathとlifecycleがgeneration追加の影響を受けない。
- `:3136-3168`: v1 adapter→core mappingとpositive。
- `:831-978`: profile mutation表へ `retryable_reason_field` を追加。
- `:2470-2492`: v2 exact profile gateを「3 field mutation」へ拡張。
- `:3000-3105`: 旧terminal APIによるv2拒否は期待値を変えず残す。

これらにより、v1については次を同時に固定する。

1. event key集合は現行 exact 24のまま。
2. retryable reason集合は空。
3. `failure_reason` とclassification reasonの等値を維持。
4. observed / terminal-failure / rejectionの既存行列を維持。
5. v1 adapter APIとcanonical lifecycle bytesを維持。
6. core変更がs8c facade bytes/signatureへ波及しない。

既存期待値を変更せず新規 assertionを足す箇所はあるが、「新fieldが増えたからv1 goldenも更新する」という変更は行わない。

## 前提 (P1)〜(P5) の検査

- **P1: 成立。** 単位1の2 file、単位2の4 file、単位3の4 fileは素集合。依存は単位1→単位2/3の1段だけ。単位2/3は統合前には互いの完成APIを仮定するが、同じfileを編集しない。
- **P2: 成立。** leafだけ、launcher/profileだけ、core/adapterだけではproduction v2 terminalは完成しない。3単位を同一waveの縦1単位として扱い、途中をland対象にしない。
- **P3: 成立。** `launch_floor_attempt()` のproduction callerは0件。現行hitは launcher自身の定義・wrapper・test seamだけ（`s8b_floor_attempt_launcher.py:723,855,879`）。実環境値域はC2まで主張しない。
- **P4: 実行 pinの追加は不要。** 新file名、`terminal_evidence_sha256`、`measurement_retry_reason`、`retryable_reason_field`、schema v2、exact evidence pathを再検索したが、production/testの既存exact pinは無い。`test_frozen_artifacts.py:41-151` の23 pathにも該当しない。`test_reflux_formal_consumer.py:26-42,1133-1151` はcore sourceをAST走査するため引き続き対象だが、新leafをその15 file集合へ加える理由はない。coreには禁止2形を書かない。
- **P4の補足:** generic receipts directoryの既存参照は `s8b_attempt_profile.py:506-523`、`test_s8b_attempt_registry.py:1621-1633`、runbook `docs/phase3-8b-restart-runbook.md:392-405` にある。いずれも新subdirectoryを禁止するexact pinではない。旧v2 schema/pathの記録はspool decisionに残るが、v3訂正文書が追記でsupersedeしているため履歴を編集しない。
- **P4のsemantic pin:** leafに `use_perf_from_receipt()` の直接callを増やすと `test_official_perf_closure.py:44-94,108-255` のinventory更新が必要になる。所有fileを増やさないため、このplanでは既存launcher gate `s8b_floor_attempt_launcher.py:565-588` を唯一の導出箇所として維持する。
- **P5: 再照準可能。** M4/M5/M6/M7/M9/M12はfinite-only、E1 precedence、digest再導出へそのまま具体化する。M1はprojected exact schema、M2は12-key bindingと`observation_event_sha256`、M3はimmutable canonical bytes、M8はcampaign実枝4/5、M10はassessed median、M11はadapter exact observation→validated capabilityへ再照準する。A案のpolicy bypass、openedだけのissuer table、全core loaderへの引数伝播を狙う旧変異は廃棄する。M13〜M18は本waveの事前登録集合へ戻さず、同等のprofile/durability検査を通常testとして置く。

## 規模の判定

1 waveに収める。

| 単位 | production | test |
|---|---:|---:|
| 単位1 leaf | +500〜700 | +550〜800 |
| 単位2 launcher/profile | +140〜220 | +350〜550 |
| 単位3 core/adapter | +420〜620 | +700〜1,000 |
| 合計 | **+1,060〜1,540** | **+1,600〜2,350** |

提示された production約+1,000〜1,600、test約+1,500〜2,400の範囲内である。単位1後に単位2/3を並列化でき、最大のadapter作業も中央loader 1本へ集約するため、依存の直列化は増えない。

上限を超えた場合でもproduction途中分割はしない。その場合は契約v3文書だけをcheckpointとして残し、半開きコードはwave成果に数えない。

## 所見

- 現物の `attempt_registry_core.py` は2,160行で、段1 brief記載の2,131行より29行多い。変更アンカー自体は一致しており、planの構造には影響しない。
- 親P-7の「新識別子のtest pinは0」は正しい。ただし識別子検索だけでは `test_official_perf_closure.py` のsemantic call inventoryを見つけられない。このplanではleafに新しいperf predicate callを置かないことで閉包を維持する。
- 契約1.1/1.5は平文群とdigest群を列挙しているが、証拠JSON内で `campaign_record` projectionをどの階層へ置くかまでは明記していない。本planは、平文24 fieldをnested `campaign_record`、6 carrier digestをnamed top-level fieldとする機械的実体化を採る。意味・受理集合・holdout-safe境界は変更しない。
- prompt冒頭はAGENTS.md所定の `単独段 dispatch: ...` 宣言形式ではなかったため、通常のclass 1 read-only導線として処理した。書込み、test、git操作は行っていない。

## 総括

単位1でcanonical evidenceとE1を固定し、その後に単位2のlauncher/profileと単位3のcore/adapterを並列実装する。v2で新しく受理するのは、exact evidenceから再導出できる契約5.2の5形だけである。v1のevent keys、語彙、分類等値、旧API、受理集合は維持する。

runnerの構造化 `execution_failure`、campaign算出変更、claim v4、`_AttemptState.mode`、core公開8 surfaceへのcapability伝播は、いずれもplanへ含めない。