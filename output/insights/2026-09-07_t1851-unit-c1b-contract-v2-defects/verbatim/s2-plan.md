# C1b 実装プラン判定

[実測] HEAD は `9c19511795` で、対象 production は leaf 不在、profile 684 行、core 2,131 行、adapter 3,122 行、launcher 909 行です。production における `launch_floor_attempt()` の呼び手と launcher module の import はともに 0 件でした。

[実測] ただし、直ちに author を開始できない契約矛盾が 4 件あります。

1. 契約表に列挙された outer field は 24 ではなく 23 個です。
2. `_finish_session()` が emit する `campaign_record` は 27/29 ではなく 30 key です。
3. 指定された `seal_terminal_evidence(reservation, opened, terminal)` の 3 引数からは、`attempt_binding` に必須の classification receipt/event と observation event の 3 digestを取得できません。
4. 現行の holdout-safe writer は、完全な `campaign_record.workload` を含む証拠文書を実データで必ず拒否します。

[推測] 以下の file:line プランは、この 4 件を裁定してから実行する条件付きプランです。未裁定のまま 24 番目の field、writer 例外、追加引数を author が発明してはいけません。

## 契約上の先行裁定

### field 数

[実測] 裁定表から抽出できる outer field は次の exact 23 個です。

```text
schema_version
attempt_binding
protocol
mode
perf_preflight_receipt
expected_use_perf
probe_before
probe_after
failure
launch_failures
throughputs
nonfinite_count
reps_expected
exec_failures
repetition_evidence
rep_integrity_failures
session_cv_max
raw_output_sha256
report_sha256
observation_sha256
finished_at
campaign_record
self_report
```

[推測] 「表の 23 語が正本で、24 は計数誤り」と裁定するか、欠落した第 24 field をユーザーが名指しする必要があります。実装側で推定追加してはいけません。

### issuer の不足入力

[実測] `FloorAttemptReservation` は `s8b_floor_attempt_launcher.py:61-81`、`OpenedFloorAttempt` は `:125-138`、`FloorAttemptTerminal` は `:141-157` ですが、いずれも次を持ちません。

```text
classification_receipt_sha256
classification_event_sha256
observation_start_event_sha256
```

[実測] この 3 値は adapter の `_AttemptState` `s8b_attempt_registry.py:181-184` にのみあり、observation digest は `_begin_attempt_observation():2388-2483` の後に確定します。

[推測] 解決案は二択です。

- 推奨: issuer を `seal_terminal_evidence(reservation, opened, terminal, observation)` に変更し、exact `CapturedObservation` の issued state を leaf が検証する。
- signature を維持する場合: launcher が observation 後に呼ぶ private binding API を追加し、その issued binding を `opened` の process-local issuer tableへ登録する。

[推測] 後者は公開 signature を守れますが、hidden API と issuer state が増えるため約 70〜110 行重くなります。

### classification reason と E2 の衝突

[実測] launcher は `s8b_floor_attempt_launcher.py:436-452,796-805` で classification reason を `competing_process` / `launch_failure` / null として固定します。一方、E2 は別語彙の 4 語です。

[実測] core は `attempt_registry_core.py:1381-1396` で terminal `failure_reason` と classification reason の等値を要求し、その後 `:1407-1408` で terminal validator を呼びます。この順序では E2 の retryable terminal はすべて validator 到達前に拒否されます。

[推測] `require_terminal_reason_equals_classification=True` 自体は維持し、capability がない経路では現行等値を維持します。capability 付き v2 だけは profile validator が classification raw reason、E2 reason、campaign reason の三者を検査してから直接等値を代替する形にします。validator 前に無条件で等値を要求する現行順序は変更が必要です。

### holdout-safe writer

[実測] `_publish_create_only()` `s8b_attempt_registry.py:1215-1250` は `admission.assert_holdout_safe_bytes()` を必ず通します。その trust root は `s8b_holdout_admission.py:1237-1269` です。

[実測] `_finish_session()` の `workload` を含む最小 canonical record を `holdout_conjunction_hits()` へ直接渡した結果は次のとおりでした。pytest は実行していません。

```text
rr80 -> {'rr80': ['terminal-evidence.json'], 'rr20': []}
rr20 -> {'rr80': [], 'rr20': ['terminal-evidence.json']}
```

[実測] `workload` は `_finish_session():6366-6367` の record 本体に含まれ、holdout scanner の三軸 regex は `s8b_holdout_freeze.py:68-74,699-711` にあります。したがって完全な `campaign_record` を現在の guarded writer で公開する実経路はありません。

[推測] full record を維持するなら、strict validation と digest 導出後の terminal-evidence 専用 publish authority が必要です。これは trust boundary の拡張なので、C1b の暗黙変更にはできません。`workload` を落とす案は exact campaign record 契約を破るため非推奨です。

## P2: campaign_record の exact 集合

[実測] `_finish_session()` `s8b_floor_campaign.py:6346-6383` の dict literal を AST で数えると exact 30 key です。

```text
attempt_id
binary_sha256_at_measure
cell_id
configuration_id
duration_s
event
excluded_reason
exclusion_class
exec_failures
holdout_id
kind
notes
probe_after
probe_before
records
rep_integrity_failures
rep_observations
reps_expected
retry
retry_ordinal
round
run_cmd
seq
session_cv
session_median
threads
throughputs
trigger
valid
workload
```

[実測] 親の 29 語は `binary_sha256_at_measure` を落としていました。裁定の 27 key はさらに過少です。`event` と `records` は `record` の直下にあり、`self._emit(record)` `:6382` へ渡されるため枠外ではありません。

[実測] 同じ 30 key は verifier trust root `_JOURNAL_KEYS["session"]` `s8b_ratified_freeze.py:262-269` にも固定されています。

[推測] leaf の `CAMPAIGN_RECORD_KEYS` はこの 30 key にし、`s8b_ratified_freeze._JOURNAL_KEYS["session"]` との集合等値を独立 test で固定します。C1b では campaign 本体を変更しません。

## file:line 実装設計

### 1. 新 leaf

[実測] `orchestrator/campaign/s8b_terminal_evidence.py` と対応 test は現在不在です。

[推測] `s8b_terminal_evidence.py:new:1-750` を次の順に置きます。

- `new:1-55`: `TERMINAL_EVIDENCE_SCHEMA = "s8b-floor-terminal-evidence/v1"`、E2 の 4 語、campaign の 4 語、outer keys、12-key attempt binding、6-key slot、30-key campaign record、3-key self report。
- `new:56-150`: frozen/slots の `TerminalEvidence`。field 集合は先行裁定後の exact 23 または名指しされた exact 24。
- `new:151-190`: `TerminalEvidenceProjection(terminal_status, failure_reason, campaign_excluded_reason, primary_value, session_median, session_cv, valid, exclusion_class)`。
- `new:191-235`: opaque `SealedTerminalEvidence` と `ValidatedTerminalEvidence(document, canonical_bytes, sha256, projection)`。通常 constructor/`replace()` では issuer table に入らない形にする。
- `new:236-350`: exact mapping、digest、text、probe、failure、repetition evidence、campaign record の parser。strict JSON、duplicate key 拒否、extra/missing key 拒否。
- `new:351-420`: throughput のみ非有限値を null に正規化し、`nonfinite_count` を再計数する pure projection。
- `new:421-500`: `s8b_floor_stats._derive_rep_integrity()` と `assess_session()` を共有する pure E1 関数。
- `new:501-610`: protocol digest、perf receipt、raw session bytes、report/observation digest、self report、campaign record の全件等値。
- `new:611-750`: issuer table、seal/require、durable bytes parser、canonical bytes/digest。

[推測] pure E1 の境界は次の形にします。

```python
def derive_terminal_projection(
    *,
    probe_before: Mapping[str, object],
    probe_after: Mapping[str, object] | None,
    failure: Mapping[str, object] | None,
    launch_failures: Sequence[Mapping[str, object]],
    throughputs: Sequence[float | None],
    nonfinite_count: int,
    reps_expected: int,
    exec_failures: int,
    rep_integrity_failures: int | None,
    session_cv_max: str,
) -> TerminalEvidenceProjection:
    ...
```

[推測] 辞書による reason 変換は持たず、campaign `s8b_floor_campaign.py:6312-6327` と同順の if/elif 6 枝にします。

[推測] canonical API は次で固定します。

```python
def canonical_terminal_evidence_bytes(
    value: TerminalEvidence | ValidatedTerminalEvidence,
) -> bytes:
    ...  # compact canonical JSON, LFなし

def terminal_evidence_sha256(
    value: TerminalEvidence | ValidatedTerminalEvidence,
) -> str:
    ...

def seal_terminal_evidence(
    reservation: object,
    opened: object,
    terminal: object,
) -> SealedTerminalEvidence:
    ...

def require_sealed_terminal_evidence(
    value: object,
) -> ValidatedTerminalEvidence:
    ...
```

[推測] crash replay 用に、strict canonical bytes から process-local validated capability を発行する private APIも必要です。一般の caller が arbitrary bytes から capability を得られる public constructorにはしません。

### 2. launcher

[実測] 変更アンカーは reservation `s8b_floor_attempt_launcher.py:61-81`、opened `:125-138`、policy gate `:508-598`、reserve forwarding `:618-644`、本体 `:723-852`、public/test entry `:855-909` です。

[推測] `OpenedFloorAttempt` は通常構築と `dataclasses.replace()` を拒否できる issued identity にし、reservation identity、probe snapshots、private sink、capture token identityを issuer tableへ登録します。

[推測] full C1b を行う場合の terminal 順序は次です。

```text
terminal_builder
→ raw output seal
→ observation-start
→ observation binding を issuer へ結合
→ seal_terminal_evidence
→ record_sealed_attempt_terminal
```

[推測] `:521-528` の v2 early gate は adapter/profile 側と同じ統合でのみ外します。分割 checkpoint では維持します。

[推測] `_reserve():628-644` は v2 のときだけ `mode=request.mode` を adapter へ渡します。v1 の呼出し shape は変更しません。

[推測] `:844-851` は schema identity で分岐し、v1 は現行 `record_attempt_terminal()`、v2 は新しい `record_sealed_attempt_terminal(observation, evidence)` を呼びます。

### 3. profile

[実測] v1 terminal key は `s8b_attempt_profile.py:445-463`、v2 additive table は `:490-504`、E2 set は `:533`、拒否 validator は `:556-563`、v2 profile は `:639-684` です。

[推測] `_S8B_V2_EVENT_KEYS` は全 event に `measurement_ordinal` を足し、terminal だけに `terminal_evidence_sha256` を足します。`_S8B_EVENT_KEYS` は一切変更しません。

[推測] `S8B_V2_RETRYABLE_FAILURE_REASONS` は exact 次集合にします。

```python
frozenset({
    "measurement_environment_conflict",
    "measurement_execution_unavailable",
    "measurement_sample_incomplete",
    "measurement_dispersion_exceeded",
})
```

[推測] `_reject_unsealed_s8b_v2_terminal()` は次の capability validator に置換します。

```python
def _require_sealed_s8b_v2_terminal(
    row: Mapping[str, Any],
    verified_terminal_evidence: object | None,
) -> None:
    ...
```

[推測] validator は row digest で exact 1 証拠を選び、status、E2 reason、primary、raw/report/observation digest、classification echo、attempt binding を再検査します。

### 4. core

[実測] `DomainProfile.terminal_row_validator` は `attempt_registry_core.py:214-216`、terminal parse は `:979-1018`、replay 呼出しは `:1402-1408`、load API は `:1455-1556`、terminal writer は `:1971-2054` です。

[推測] validator type を次へ変更します。

```python
terminal_row_validator: (
    Callable[[Mapping[str, Any], object | None], None] | None
)
```

[推測] `_assert_registry_rows_with_budget_counts()`、`assert_registry_rows()`、両 load APIへ keyword-only `verified_terminal_evidence: object | None = None` を通します。

[推測] 既存 terminal を含む v2 台帳へ別 slot を append できるよう、`reserve_attempt_slot():1696`、`classify_attempt():1812`、`begin_attempt_observation():1913`、`record_attempt_terminal():1971`、`record_attempt_recovery():2057` にも同じ keywordを伝播します。terminal writerだけの変更では、次の操作で既存 terminal の replay が再び閉じます。

[推測] `_parse_row():979-1018` は expected key に `terminal_evidence_sha256` が存在するときだけ non-null SHA-256 を要求します。

[推測] `record_attempt_terminal()` は次を追加します。

```python
terminal_evidence_sha256: str | None = None,
verified_terminal_evidence: object | None = None,
```

[推測] v1 schemaで digest が渡された場合は拒否し、v2 schemaでは digest と capability の両方を必須にします。

[推測] classification reason の直接等値は capability なしでは現行どおりです。capability 付き v2 だけ profile validator の三者再導出成功を条件に差を許します。

### 5. adapter

[実測] 主要アンカーは issued handle `s8b_attempt_registry.py:164-316`、profile exact comparator `:319-486`、nofollow reader `:582-635`、prefix replay `:857-978`、create-only publisher `:1215-1250`、claim `:1413-1572`、atomic update `:1666-1810`、state reserve `:1888-2056`、terminal API `:2536-2658`、resume `:2706-3122` です。

[推測] `:42-71` に terminal-evidence dir/schema関連定数と evidence-first crash fault point を追加します。

[推測] `_AttemptState:164-185` と `_state_fingerprint():229-255` に v2 `mode` を追加します。v1 は `None` 固定にします。

[推測] durable claimへ mode を残すため、`_CLASSIFICATION_CLAIM_V3_SCHEMA` を無断で同名変更せず、v2 claim v4 を追加します。`_claim_document():1440-1473`、exact keys `:1476-1500`、reader `:1503-1572`、resume state `:2921-3075` を同時更新します。

[推測] `:1413-1437` と同じ nofollow path disciplineで次を追加します。

```python
def _terminal_evidence_path(root: Path, digest: str) -> Path:
    return root / "floor-attempt-registry-receipts" / \
        "terminal-evidence" / f"{digest}.json"
```

[推測] terminal digestを含む registry snapshotから全 evidence fileを読み、filename、bytes digest、strict JSON、exact keys、canonical bytesを検査する helperを新設します。

[実測] capability を通すべき現行 load call は 8 call、6 surfaceです。

- prefix: `:974`
- cross-generation budget: `:1647`
- atomic old/candidate: `:1687,1698`
- public read: `:1883`
- reserve/observation snapshot: `:1942,2439`
- resume: `:2791`

[推測] 各 surfaceに evidence 正例と欠落/不一致負例を 1 対 1 で置きます。genesis-only `:810,1841` は terminal が存在しないため capability 不要です。

[推測] `_atomic_update_locked():1666-1736` の transition は validated evidence集合も受け取る形にし、すべての nested transition が coreへ明示転送します。

[推測] `record_sealed_attempt_terminal()` は `record_attempt_terminal():2544-2603` の直後に置きます。

```python
def record_sealed_attempt_terminal(
    observation: CapturedObservation,
    evidence: object,
) -> None:
    ...
```

[推測] この API は v2 exact handleだけを受け、terminal valuesを引数として受けません。証拠から導出した status/reason/primary/digestだけを coreへ渡します。

[推測] candidateを memory validationした後、`prepare()` で evidenceを `allow_exact_retry=True` により公開し、その後に registry stagingを行います。evidence fileのみ残る crash は許容し、rowのみ残る順序は作りません。

[推測] 現行 `record_attempt_terminal()` と `record_classified_failure_terminal()` の v2 拒否 `:2536-2541,2614-2615` は残します。

## v1 / v2 の受理集合

### v1

[実測] 現行 v1 event key は `s8b_attempt_profile.py:403-477`、retryable reason は空 `:532`、terminal null matrix は `attempt_registry_core.py:1021-1071` です。

[推測] 変わる点はありません。v1 terminal key に digestを足さず、E2 を与えず、旧 adapter API、classification reason等値、terminal status/null matrixを維持します。

[推測] 新しい core optional keywordを使わない既存呼出しの結果と gate 順序を golden testで固定します。v1 に `terminal_evidence_sha256` を渡した場合は extra capabilityとして拒否します。

### v2

[実測] 現在は profile validatorにより terminal 全件が拒否され、observation-startまでしか到達できません。

[推測] 変わる点は、sealed capabilityで再導出できる次の terminalだけが追加受理されることです。

- `observed`、reason null、primary は `assess_session.median`
- `retryable-failure`、reason は E2 の exact 4 語、primary/observation digestは null

[推測] 変わらない点は、通常 core 直呼び、旧 adapter API、証拠欠落/不一致、`terminal-failure`、`not-consumed`、classification echo改変が拒否されることです。

[実測] `retryable_terminal_opens_next_attempt=False` は profile `:672` にあり、E2 terminalが recovery ordinalを開かない性質も維持されます。

## P3: 到達性と述語の強さ

[実測] production caller 0 のため、次の 16 outer fieldは実環境 instanceの値域が C2 まで未観測です。

```text
attempt_binding
protocol
mode
perf_preflight_receipt
probe_before
probe_after
failure
launch_failures
throughputs
repetition_evidence
session_cv_max
report_sha256
observation_sha256
finished_at
campaign_record
self_report
```

[実測] 残る `schema_version`、`expected_use_perf`、`nonfinite_count`、`reps_expected`、`exec_failures`、`rep_integrity_failures`、`raw_output_sha256` は constantまたは他 fieldから再導出できます。ただし実際の値は未観測です。

[推測] 本 waveで許される強い述語は、exact key/type、既存 closed literal、SHA-256 shape、既存 validator共有、source間等値、算術的不変条件、E1再導出だけです。

[推測] 採用しない述語は、新しい最大文字数、probe rc の新しい範囲、timestampの新書式、throughputの正値限定、duration非負、run_cmdの追加形式、例外名/errnoのallowlistです。いずれも production launcher経路で到達性が実測されていません。

[実測] `repetition_evidence` の現行 sourceは runner `capture_measure_point():803-1054` で、open時に reps 本の 6-key recordを作ります。一方、既存 `_derive_rep_integrity():471-589` は不正 recordを理由へ落とすため、leafが独自に過剰拒否せずこの関数の再導出結果を使います。

## P5: pin 閉包

[実測] 指定 3 literalの `git grep` は production/testで 0 件でした。hitは decision fragmentと既存 C1a insight文書だけです。一般語 `terminal-evidence` の production hitは `floor_liveness.py:446` と `tools/pegasus/dispatch_compute.py:2128` の無関係な reason文字列 2 件です。

[実測] `test_frozen_artifacts.py:41-151` の `FROZEN_MANIFEST` は exact 23 output pathで、production source、shared admission root、terminal evidence pathを含みません。ここへ追加する bytes pin は 0 件です。

[実測] source-name inventoryの該当は次の 3 testです。

- `test_ccbench_spawn_sites.py:212`: launcher `_owned_post_probe` 1 call。C1bで subprocess siteを増やさないため不変。
- `test_official_perf_closure.py:44-94,108-255,270-310`: leafが `use_perf_from_receipt()` を呼ぶと production file/predicate/guard inventoryへ追加が必要。
- `test_reflux_formal_consumer.py:25-41,1084-1102`: core sourceを読むが、bytes hash pinではなく禁止 surface scan。通常は変更不要。

[実測] path検索では出ない semantic trust rootは次です。

- canonical bytes: `attempt_registry_core.py:219-228`
- v2 event keys/retry vocabulary: `s8b_attempt_profile.py:490-533`
- session exact 30 key: `s8b_ratified_freeze.py:262-269,1986-2012`
- E1 stats: `s8b_floor_stats.py:127-165,471-589`
- perf receipt: `perf_preflight.py:179-270`
- protocol digest: `s8b_floor_contract.py` の `canonical_protocol_sha256`
- holdout-safe write: `s8b_holdout_admission.py:1237-1329`

[推測] よって P5 の「凍結 bytes は増えない」は `FROZEN_MANIFEST` に限れば正しい一方、pin閉包全体として 0 件という結論は誤りです。少なくとも official perf closureと上記 semantic trust rootsの直接 testが必要です。

## test 配置

[実測] 現行は launcher 1,208 行/23 test関数、adapter 3,707 行/75、core/profile 2,562 行/68、official perf closure 950 行/7です。

[推測] 新規・更新 testは次へ置きます。

- `test_s8b_terminal_evidence.py:new`: exact field/binding/campaign keys、strict JSON、canonical bytes、nonfinite normalization、E1 6枝、cross-field、issuer forgery、digest derivation。
- `test_s8b_floor_attempt_launcher.py:101-182,219-302,892-956`: fakeに sealed APIを追加し、v1は旧API、v2は新API、issued opened identity、terminal前後順序を検査。
- `test_attempt_registry_core_s8b_profile.py:2172-2380`: E2 exact set、v1 key不変、v2 terminal key、capabilityなし拒否、専用 lower path正例、reason三者経路。
- `test_s8b_attempt_registry.py:2412-2492,3000-3105,3136-3168,3215-3633`: durable artifact、crash順序、mode claim、load全surface、旧API拒否。
- `test_official_perf_closure.py:44-94,108-255,270-310`: leaf file、`use_perf_from_receipt` predicate、official/mismatch guardを登録。
- `test_s8b_ratified_verify.py`、`test_frozen_artifacts.py`、`test_ccbench_spawn_sites.py`:変更 0、既存 trust rootの対照として走らせる。

## 規模見積りと P1

| file | 現行 [実測] | 追加見積り [推測] |
|---|---:|---:|
| `s8b_terminal_evidence.py` | 不在 | +560〜740 |
| `s8b_floor_attempt_launcher.py` | 909 | +85〜135 / -8〜15 |
| `s8b_attempt_profile.py` | 684 | +28〜42 / -8〜12 |
| `attempt_registry_core.py` | 2,131 | +125〜180 |
| `s8b_attempt_registry.py` | 3,122 | +430〜620 |
| `test_s8b_terminal_evidence.py` | 不在 | +650〜900 |
| `test_s8b_floor_attempt_launcher.py` | 1,208 | +180〜260 |
| `test_attempt_registry_core_s8b_profile.py` | 2,562 | +230〜330 |
| `test_s8b_attempt_registry.py` | 3,707 | +700〜950 |
| `test_official_perf_closure.py` | 950 | +15〜25 |

[推測] 合計は production +1,228〜1,717、test +1,775〜2,465 です。C1a 実績 production +245 / test +582 の約 3.7〜5.1 倍です。

[推測] P1 の full 3-child waveは規模上限超過として採りません。契約矛盾の裁定後、C1b は leaf + unit1 の 2 子に切り、unit2を C1cへ送るのが最小です。

- child 1: leaf、leaf test、official perf closure。
- child 2: launcher、launcher test。
- C1c: profile、core、adapter、core/profile test、adapter test。

[推測] この分割中は launcher `:521-528` の早期 gateと profile `:556-563` の無条件拒否を残すため、v2 terminalは開かないままです。unit2まで揃う前に「terminalが有効」と記録してはいけません。

## 変異候補 18 件

| ID | 変異箇所 | KILLED期待 node | 他 gateに遮られない理由 |
|---|---|---|---|
| M1 | [推測] leaf: outer exact keys | `test_terminal_evidence_outer_keys_are_exact` | [推測] parser直呼びで他 fieldをvalid固定 |
| M2 | [推測] leaf: attempt binding exact keys | `test_attempt_binding_rejects_each_missing_or_extra_key` | [推測] binding 1 keyだけを変える |
| M3 | [推測] leaf: canonical bytesへLF追加/spacing変更 | `test_canonical_bytes_and_digest_are_independently_pinned` | [推測] serializer直呼びでadapter不使用 |
| M4 | [推測] leaf: nonfiniteをnull化しない | `test_nonfinite_throughput_is_null_and_counted` | [推測] normalization単体、JSON gate前に観測 |
| M5 | [推測] leaf E1: competitionをlaunch後へ移動 | `test_e1_competition_precedes_launch_failure` | [推測] 両条件trueのpure入力 |
| M6 | [推測] leaf E1: failure/full launch branch削除 | `test_e1_full_execution_unavailable` | [推測] competition false、他理由なし |
| M7 | [推測] leaf E1: partial execをsample incompleteへ変更 | `test_e1_partial_exec_uses_execution_unavailable` | [推測] `0 < exec < reps`だけ成立 |
| M8 | [推測] leaf E1: integrity/nonfinite branch削除 | `test_e1_sample_incomplete_from_each_raw_cause` | [推測] 各paramで原因を1個だけ成立 |
| M9 | [推測] leaf E1: dispersionをobservedへ変更 | `test_e1_dispersion_exceeded_from_assessment` | [推測] complete finite高CV vectorを使用 |
| M10 | [推測] leaf E1: observed primaryをself reportから採用 | `test_e1_observed_primary_is_assessed_median` | [推測] self reportだけ異なるpure fixture |
| M11 | [推測] leaf issuer: constructor/replace forged openedを受理 | `test_seal_requires_exact_issued_opened_identity` | [推測] valid issued正例後にidentityだけ交換 |
| M12 | [推測] leaf seal: terminal report digestを信頼 | `test_seal_rederives_raw_report_and_observation_digests` | [推測] terminal同名値だけ変更 |
| M13 | [推測] profile `:533`: E2 1語欠落/余分語追加 | `test_v2_retryable_vocabulary_is_exact_and_v1_empty` | [推測] 定数/profile直検査 |
| M14 | [推測] profile `:490-504`: v2 terminal digest key削除 | `test_v2_terminal_event_adds_only_evidence_digest` | [推測] schema table直検査 |
| M15 | [推測] core `:1407-1408`: capabilityなしでvalidatorを通す | `test_v2_core_direct_terminal_requires_capability` | [推測] 標準 lifecycleを完全validにして専用gateへ到達 |
| M16 | [推測] core `:1971-2054`: row digestとcapability digestの束縛削除 | `test_lower_core_path_binds_exact_validated_evidence` | [推測] capability中のdigestだけ交換 |
| M17 | [推測] adapter terminal `prepare`: rowをevidenceより先に公開 | `test_terminal_evidence_publish_precedes_registry_staging` | [推測] evidence公開直後faultでfile-only状態を直接観測 |
| M18 | [推測] adapter load helper: 8 callの1つでevidence再読を省略 | `test_each_durable_load_surface_requires_terminal_evidence` | [推測] surface別paramで対象操作だけを呼び、他loadを経由させない |

## 総括

- [実測] P1: full 3子は規模超過。裁定後は leaf + unit1 の2子、unit2はC1c。
- [実測] P2: campaign recordは27/29でなくexact 30 key。`event` / `records`も含む。
- [実測] P3: production caller 0。16 outer fieldの実環境instanceはC2まで未観測。
- [実測] P4: E2の4語はv2だけ、v1 retryable setは空のまま。
- [実測] P5: `FROZEN_MANIFEST`追加は0だが、perf closureとsemantic trust rootがあるため「閉包0」は棄却。
- [実測] 契約表は24でなく23 fieldを列挙しており、24番目の裁定が必要。
- [実測] 3引数issuerはattempt bindingの3 digestを取得できない。
- [実測] full campaign recordは現行holdout-safe writerに実データで拒否される。
- [推測] 見積りはproduction +1,228〜1,717、test +1,775〜2,465。
- [推測] 実装子はC1b 2本。所有はleaf系、launcher系。core/profile/adapter系1本はC1c。
- [推測] C1c統合までv2 terminalは開かない。
- [推測] 変異候補は18件。