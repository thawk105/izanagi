[実測] 指定資料を順番どおり読了し、HEAD `04f06d0326eaf9fad51a3c698b2b3a5e5b062e77` のコードを静的検査した。pytest は実行していない。test node 数は AST で `parametrize` を展開して数えた。

# 1. terminal 証拠の契約の検証

## 結論

[実測] 親案の 14 field だけでは不足する。最低でも `protocol`、`perf_preflight_receipt`、`open_failure`、`campaign_record`、`finished_at` の 5 field を追加する必要がある。

[実測] 特に `open_failure` が無いと `OpenedFloorAttempt.open_error` からの `measurement_execution_unavailable` を再生時に再導出できず、`campaign_record` が無いと registry terminal 済み、journal session 未記録の crash cut から exact session line を復元できない。

[推測] 採用する exact field 集合は次の 19 field とする。

```text
schema_version
protocol
expected_use_perf
perf_preflight_receipt
mode
probe_before
probe_after
launch_failures
open_failure
throughputs
reps_expected
exec_failures
repetition_evidence
rep_integrity_failures
session_cv_max
raw_output_sha256
finished_at
campaign_record
self_report
```

## field 別検証

| field | 現物からの取り口と判定 |
|---|---|
| `schema_version` | [実測] launcher 内の定数から固定できる。campaign 入力は不要。 |
| `expected_use_perf` | [実測] `orchestrator/calibrator/perf_preflight.py:261-270` の `use_perf_from_receipt()` を launcher から直接 import できる。`perf_preflight` は `runner.PERF_EVENTS` だけを importし、`runner` は launcher を import しないため循環しない。 |
| `mode` | [実測] 現 launcher には無いので C2 が reservation の識別入力として渡す必要がある。値域は campaign と同じ `{"pilot","official"}`。`_assert_perf_mode()` の official 制約は `s8b_floor_campaign.py:448-455`。 |
| `probe_before` | [実測] 現 launcher は所有していない。`_launch_floor_attempt():582-590` の reserve 後、capture 前へ、既存 `_owned_post_probe():238-267` と同じ capability を使って挿入できる。 |
| `probe_after` | [実測] 現 `post_probe` で取得できる。exact `{rc,stdout,stderr,competing}` は `_post_probe():226-235` を強化して固定する。pre-probe 競合時だけ null。 |
| `launch_failures` | [実測] `CapturedMeasurement.launch_failures` は open 前に読める唯一の token surface である。型は `runner.py:62-102`、launcher の射影は `:321-359`。 |
| `throughputs` | [実測] `token.open()` の実体は `ScalePoint` で、実名 attribute は `ScalePoint.throughputs` (`calibrator/model.py:55-76`)。launcher は private rep sink と `_derive_rep_integrity()` の qualified 列を照合して証拠へ入れる。 |
| `reps_expected` | [実測] `ScalePoint` 自身には無い。C2 から渡す normalized protocol の `protocol["reps"]` からしか取れない。capture kwargs の `reps` と equality を要求する。 |
| `exec_failures` | [実測] 現 campaign は `ScalePoint.notes` を `_count_exec_failures()` (`s8b_floor_campaign.py:1879-1890`) で数える。launcher は同じ固定 regex を内部実装し、open 失敗時は `reps_expected` とする必要がある。 |
| `repetition_evidence` | [実測] `capture_measure_point(..., rep_observations=list)` は実在する (`runner.py:803-824`)。sink は `open_measurement_point()` に入ってから初期化・更新される (`:933-1049`) ため、snapshot は `durable.open()` (`launcher.py:616-619`) の後でなければならない。 |
| `rep_integrity_failures` | [実測] `s8b_floor_stats._derive_rep_integrity()` (`:471-589`) から機械導出できる。pre-probe skip と open failure は null、opened measurement は exact int とする。 |
| `session_cv_max` | [実測] measurement からは取れない。normalized protocol の `protocol["session_cv_max"]` が必要で、`assess_session()` の入力になる (`s8b_floor_stats.py:127-165`)。 |
| `raw_output_sha256` | [実測] launcher は `FloorAttemptTerminal.raw_output_bytes` (`launcher.py:125-141`) から計算でき、adapter は deferred reader から別に再計算して `_AttemptState.raw_output_sha256` へ保存する (`s8b_attempt_registry.py:2379-2385`)。両者の equality を要求できる。 |
| `self_report` | [実測] `terminal_status` と `primary_value` は `FloorAttemptTerminal`、`excluded_reason` は `FloorAttemptTerminal.campaign_record` から得る。3 値は証拠へ写すが、row の導出入力には使わず、同じ raw facts からの再導出との比較専用にする。 |

## 追加 field

| 追加 field | 理由 |
|---|---|
| `protocol` | [実測] `reps_expected` と `session_cv_max` だけでは、crash 後にその値が protocol 由来か証明できない。normalized protocol 全体を入れ、`canonical_protocol_sha256()` (`s8b_floor_contract.py:573-585`) が registry binding の `protocol_sha256` と一致することを要求する。 |
| `perf_preflight_receipt` | [実測] `expected_use_perf` だけでは replay 時に bool を再導出できない。normalized receipt または null を保存し、毎回 `use_perf_from_receipt()` を再実行する。 |
| `open_failure` | [実測] `OpenedFloorAttempt.open_error` (`launcher.py:117-122,614-619`) が親案から欠落している。exact `null | {exception_type, errno, message}` とする。 |
| `campaign_record` | [実測] `FloorAttemptTerminal.campaign_record` は既に存在するが未使用 (`launcher.py:141`)。これを保存しないと terminal-first crash から journal session を復元できない。 |
| `finished_at` | [実測] sealed API を `(observation, evidence)` の 2 引数だけにするなら、core terminal の必須 field `finished_at` (`attempt_registry_core.py:1976,1999`) も evidence に必要。 |

[実測] 削除すべき親案 field は無い。`expected_use_perf`、`reps_expected`、`session_cv_max` は追加した antecedent と重複するが、replay で equality を強制する機械導出 mirror として残せる。

## protocol と D1113

[実測] v2 reservation は binding の protocol と admission claim を `_measurement_generation_claim_digest_from_v2_payload()` で照合し (`s8b_attempt_registry.py:1932-1963`)、marker 所有の更新だけを通す (`:2001-2027`)。

[推測] C2 は normalized protocol、mode、normalized perf receipt、consumption marker を `FloorAttemptReservation` に入れる。launcher は副作用前に protocol digest、capture の `reps` / `use_perf`、receipt から再導出した bool を照合する。したがって campaign が bool、reps、CV 閾値を独立に選ぶ面は作らない。

## pre-probe と private sink

[実測] 現 campaign は `strict_probe()` 後、競合なら `measure_fn` を呼ばずに終了する (`s8b_floor_campaign.py:6241-6255`)。したがって P2 の `reserve → pre-probe → competing なら capture 無し` は現挙動と一致する。

[実測] spawn-site pin は `_owned_post_probe` 内の `subprocess.run` 1 箇所を数えている (`test_ccbench_spawn_sites.py:212`)。同じ関数を前後 2 回呼ぶだけなら静的 site 数は 1 のままで、pin の変更は不要。

[実測] `_CERTIFIED_MEASUREMENT_KEYWORDS` (`launcher.py:32-46`) に `rep_observations` を追加する必要はない。`_capture():429-441` が caller kwargs の allowlist 検査後に launcher 私有 list を明示引数として足せる。

## 再導出 policy と classification equality

[実測] 現 core は v2 terminal について、まず `pre_observation_failure_reason_echo` と classification reason を比較し (`attempt_registry_core.py:1381-1388`)、続いて `failure_reason` も同じ文字列であることを要求する (`:1389-1396`)。

[実測] E2 の `measurement_environment_conflict` と classification の `competing_process` は文字列一致しないため、現 policy のままでは正しい evidence terminal が必ず拒否される。

[推測] 選択肢 (b) を採る。v2 factory だけ `require_terminal_reason_equals_classification=False` とし、echo equality は維持する。adapter は evidence bytes から次の 3 値を独立に再導出して比較する。

1. [推測] classification reason: probe competition、launch failure、または null。
2. [推測] terminal E2 reason: raw facts から 4 語または null。
3. [推測] campaign excluded reason:同じ raw facts から凍結 4 語または null。

[推測] `excluded_reason → E2` の変換表は作らない。各 precedence branch が raw facts から E2 と campaign reason を別々に返し、self-report は最後に equality 比較する。これが D1113 の「辞書を権威にしない」と両立する。

[実測] 選択肢 (a) は現 core では成立しない。`terminal_row_validator` は row 1 件しか受けず (`DomainProfile:214-216`, replay `:1407-1408`)、外部 evidence file や対応 classification rowを読めない。

## status と E2

[推測] 再導出順は次で固定する。

```text
probe_before.competing or probe_after.competing
  -> retryable-failure / measurement_environment_conflict

open_failure != null
or (launch_failures != [] and exec_failures >= reps_expected)
  -> retryable-failure / measurement_execution_unavailable

0 < exec_failures < reps_expected
or rep_integrity_failures > 0
or assess_session.required_reason == nonfinite_or_partial_output
  -> retryable-failure / measurement_sample_incomplete

assess_session.required_reason == performance_anomaly
  -> retryable-failure / measurement_dispersion_exceeded

otherwise
  -> observed / null / assess_session.median
```

[実測] v2 は `retryable_terminal_opens_next_attempt=False` (`s8b_attempt_profile.py:672`) なので、`retryable-failure` は recovery `attempt_ordinal` を開かない。`max_series_attempts=None` でも closed genesis slot 集合と cell-wide `_s8b_v2_budget_key()` (`:550-553`) が start 数を制限する。

[実測] `0 < exec_failures < reps` かつ完全 throughput という矛盾入力について、現 campaign は `launch_failure` にする (`s8b_floor_campaign.py:6318-6322`) が親案は sample incomplete とする。C2 の terminal builder は C1 契約へ合わせる必要がある。

[実測] canonical JSON は NaN/Inf を保存できず、実 runner も `_num()` で非有限値を `None` へ落とし (`benchparse.py:39-50`)、`ScalePoint.throughputs` には non-null だけを積む (`runner.py:1003-1023`)。したがって production の非有限値は `len(throughputs) != reps` として sample incomplete に届く。evidence 内に直接 NaN/Inf がある入力は schema rejection とする。

## raw output と self-report

[推測] `campaign_record` は session mapping 全体とし、`serialize_session_line(campaign_record)` (`s8b_attempt_profile.py:566-577`) が `raw_output_bytes` と byte-for-byte 一致しなければ封印しない。

[推測] row の `report_sha256` は raw session line の digest、`observation_sha256` は observed 時だけ canonical `repetition_evidence` の digest、`primary_value` は `assess_session().median` から導出する。terminal builder の同名値は equality 比較だけに使う。

## durable bytes の規則

[推測] crash 後の権威規則は次の 3 行で固定する。

1. [推測] evidence は `canonical_json_bytes(document)` の LF 無し bytes とし、SHA-256 を `terminal_evidence_sha256` とする。
2. [推測] row digest が指す no-follow regular fileを root lock 下で読み、filename、bytes digest、strict JSON、exact keys、canonical bytes を検査する。
3. [推測] file bytesから再導出した status、reason、primary、raw/report/observation digest、classification reason が row と一致した場合だけ受理する。

[推測] 保存先は既存 receipts dir 配下の `floor-attempt-registry-receipts/terminal-evidence/<digest>.json` とし、`_publish_create_only(..., allow_exact_retry=True)` を使う。

[実測] `_atomic_update_locked()` は `prepare()` を registry staging より前に実行する (`s8b_attempt_registry.py:1713-1722`)。ここで evidence を fsync 済み create-only 公開し、その後に terminal row を replace できる。crash 時は「orphan evidence」か「evidence + terminal row」のどちらかになり、evidence 欠落の terminal row は作られない。

# 2. 規模の実測と分割判定

## production 規模

| 群 | production file / 現行 symbol | 見積り | 単独整合 |
|---|---|---:|---|
| launcher pre-probe / sink | [実測] `s8b_floor_attempt_launcher.py`: reservation `:54-69`、probe `:226-318`、external evidence `:362-385`、capture `:408-441`、launch `:548-701` | [推測] 追加 120-170、変更 60-90、削除 20-35 行。現 `_launch_floor_attempt` 自体が 98 行。 | [推測] 可能。v2 terminal は従来どおり閉じたまま、v1 terminal を維持できる。 |
| sealed evidence handle | [推測] 新設 `s8b_terminal_evidence.py`: exact parser、projection、`SealedTerminalEvidence`、seal/open | [推測] 追加 240-320 行。根拠は既存 `_derive_rep_integrity` 119 行、`assess_session` 39 行、probe/failure/canonical helper 約 60 行。 | [推測] 単独 active 化は不可。adapter API と同時に束ねる。 |
| core field / row validator | [実測] `attempt_registry_core.py`: `_parse_row():829-1018`、terminal replay `:1332-1409`、`record_attempt_terminal():1971-2054` | [推測] 追加 18-28、変更 10-18、削除 2-5 行。 | [推測] schema 追加自体は加法的だが、E2/profile/adapter と別 commitにはしない。 |
| adapter sealed API / artifact | [実測] `s8b_attempt_registry.py`: `_publish_create_only():1215-1250`、`_atomic_update_locked():1666-1736`、artifact precedent `:2059-2144`、terminal APIs `:2510-2658` | [推測] 追加 180-250、変更 35-55、削除 8-15 行。 | [推測] handle、core field、profile validator が必須。 |
| profile E2 / validator | [実測] `s8b_attempt_profile.py`: v2 event keys `:490-503`、E2 set `:532-537`、stub `:556-563`、v2 factory `:639-684` | [推測] 追加 15-25、変更 12-20、削除 8-12 行。 | [推測] E1 validator と同じ commit でだけ可能。 |
| test | [実測] production 変更なし。既存 file は launcher 682 行、adapter 3,707 行、core/profile 2,562 行、spawn inventory 3,513 行。 | [推測] test 追加 850-1,250 行、既存変更 180-300 行。 | [推測] production 群と同時。 |

[推測] production 全体は追加 573-793、既存変更 127-183、削除 38-67 行、test 込みの changed LOC は約 1,600-2,300 行になる。

## 現存 test node の実測

[実測] 現在の node 数は次のとおり。

| file | test 関数 | parametrize 展開後 node |
|---|---:|---:|
| `test_s8b_floor_attempt_launcher.py` | 7 | 12 |
| `test_s8b_attempt_registry.py` | 75 | 111 |
| `test_attempt_registry_core_s8b_profile.py` | 68 | 108 |
| `test_ccbench_spawn_sites.py` | 43 | 44 |

[実測] launcher の 12 node は次の 7 定義である。

- [実測] `test_mut_t1668_seal_order_and_reason_precedence_use_recorder_fake` 3 node (`:268`)。
- [実測] `test_open_error_still_observes_and_terminalizes_after_classification` 1 node (`:362`)。
- [実測] `test_empty_output_cannot_reach_observation_or_terminal` 1 node (`:424`)。
- [実測] `test_existing_genesis_replays_all_rows_and_rejects_a_different_slot_set` 1 node (`:472`)。
- [実測] `test_real_adapter_creates_and_exactly_reuses_complete_genesis` 1 node (`:510`)。
- [実測] `test_certified_measurement_keywords_reject_result_leak_surfaces` 4 node (`:609`)。
- [実測] `test_certified_api_rejects_a_caller_callable_post_probe_without_effects` 1 node (`:648`)。

[実測] adapter の `record_attempt_terminal` は helper/direct callを通じて既存 13 nodeから参照されている。対象は `:427`, `:462`, `:502` の 2 node、`:532`, `:621`, `:1240`, `:1311`, `:1506`, `:1877`, `:1972`, `:3000`, `:3136` の各 nodeである。v2 は `:3000` の 1 nodeだけで、残り 12 nodeは v1 回帰 pin である。

[実測] core の S8B `_terminal()` helperを使う既存 nodeは 12 件で、定義位置は `test_attempt_registry_core_s8b_profile.py:689,720,761,792,1170,1193,1270,1297,1478,1709,2251,2383` である。

[実測] core `record_attempt_terminal()` の別 domain 回帰は S8C 8 node、equivalence 1 node、`test_trial_registry.py` 7 nodeの計16 nodeである。新引数は default 付きにし、これらを変更しない。

[実測] v2 terminal に直接関係する現存 pin は次の 4 nodeである。

- [実測] `test_v2_profile_is_additive_empty_retryable_and_budgeted_by_cell` (`test_attempt_registry_core_s8b_profile.py:2172`)。
- [実測] `test_profile_extension_fields_are_keyword_only_and_preserve_legacy_defaults` (`:2219`)。
- [実測] `test_terminal_validator_direct_replay_and_producer_mapping_keep_v1_positive` (`:2251`)。
- [実測] `test_v2_marker_claim_v3_resume_and_legacy_terminal_fail_closed` (`test_s8b_attempt_registry.py:3000`)。

[実測] B2/D1 の proof 型 pin 19 node (`test_attempt_registry_core_s8b_profile.py:2455-2558`) と prefix inspector pin 22 node (`test_s8b_attempt_registry.py:3216-3703`) は terminal 行をまだ作らず、変更禁止の回帰集合である。

[実測] spawn-site 在庫を検査する node は `test_reviewed_ccbench_measurement_launches_use_bounded_sites` (`test_ccbench_spawn_sites.py:3414`) の 1 nodeである。同じ `_owned_post_probe` siteを再利用すれば更新不要。

[推測] 新設 node は launcher/evidence 22、core/profile 12、adapter/artifact 20の計54 nodeを基準にする。既存更新は launcher 12、core/profile 3、adapter 1の計16 nodeである。

## 1 wave 判定

[推測] P5 の「実装子2本、fix3巡以内で1 wave」は採らない。B2/D1 の実績 1,760 行に近いか上回り、A2α は同規模で fix 5巡を要した。今回は process ordering、外部 artifact、core/profile schema の3面が結合するため、fix 3巡以内を安全側には主張できない。

[推測] 分割は次の1案に絞る。

1. [推測] `C1a`: launcher の pre-probe、capture skip、private sink、reservation の C2 入力面、`OpenedFloorAttempt` raw factsまで。v2 terminal は従来の無条件拒否のまま。実装子1本。
2. [推測] `C1b`: `SealedTerminalEvidence`、E1/E2、core field、adapter sealed API、durable artifact、launcher の v2 call切替。実装子2本。

[推測] C1a 単独時も v1 production pathは整合し、v2 は従来どおり閉じ、既存 testを緑にできる。C1b との境界は本 plan の reservation field、`OpenedFloorAttempt` field、handle型、sealed API signatureで固定できる。

[推測] C2 から C1 へ追加する余裕はない。producer capture thin wrapperも本 waveへ前倒ししない。

# 3. 実装プラン

## 1. `SealedTerminalEvidence` と seal

[推測] 新設 `orchestrator/campaign/s8b_terminal_evidence.py` に次の carrier を置く。

```python
@dataclass(frozen=True, slots=True, init=False)
class SealedTerminalEvidence:
    _canonical_bytes: bytes = field(repr=False)
    _sha256: str
    _seal: object = field(repr=False, compare=False)
```

[推測] `_seal_terminal_evidence(document)` は exact schema検査、再導出、canonical 化後だけ module-local sealを付ける。`_require_sealed_terminal_evidence()` は `type(value) is SealedTerminalEvidence`、seal identity、bytes digest、canonical parseを再検査する。

[推測] `FloorPostProbeCapability` の現行 exact type + seal + fixed callable 検査 (`launcher.py:284-306`) と同じ形にする。

[推測] launcher は `terminal_builder(opened)` (`launcher.py:628`) 後に `raw_output_bytes` を `_OwnedRawOutput.seal()` (`:633`) へ入れ、その後 handleを発行する。handleは adapterへだけ渡し、`FloorAttemptLaunchResult` (`:145-149`) へ追加しない。

## 2. launcher の流れ

[推測] `FloorAttemptReservation` (`launcher.py:54-69`) を次のように拡張する。

```python
slot_id:
    tuple[str, str, int, int]
    | tuple[str, str, int, int, int]
protocol: Mapping[str, object]
mode: str
perf_preflight_receipt: Mapping[str, object] | None
consumption_marker: object | None
```

[推測] `_reserve():444-469` は `consumption_marker=request.consumption_marker` を adapterへ渡す。v1 は None、v2 は B1 capabilityを要求する。

[推測] `_launch_floor_attempt():548-645` の順序を次へ変更する。

```text
validate immutable policy inputs
ensure genesis
reserve
probe_before
if competing:
    captureなし
    probe_after=None
    launch_failures=()
else:
    private rep sink生成
    capture(..., rep_observations=private_sink)
    probe_after
classify
token.open または open_failure
private sink snapshot
terminal_builder
raw output seal
evidence seal
begin observation
record_sealed_attempt_terminal
return opened + terminal only
```

[推測] `_external_evidence_sha256():362-375` は `probe_before`、nullable `probe_after`、`launch_failures` の canonical payloadへ変更する。adapter の artifact検査も同じ関数から digestを再導出して classification rowと比較する。

[推測] `_pre_observation_failure_reason():378-385` は `probe_before.competing or probe_after.competing` を最優先、次に `launch_failures`、最後に nullとする。`open_failure` は classification 後の事実なので classification reasonには使わない。

[推測] `OpenedFloorAttempt` (`:114-122`) は `post_probe` を `probe_before` / `probe_after` に分け、`repetition_evidence` snapshotを足す。

[推測] `_launch_floor_attempt_for_test():673-701` は1つの probe callableを複数回返せる seamへ維持し、pre/post別 callableは許さない。sequenceを返す test doubleで前後を区別する。

## 3. sealed API

[推測] `s8b_attempt_registry.py:2536-2602` の隣に次を置く。

```python
def record_sealed_attempt_terminal(
    observation: CapturedObservation,
    evidence: SealedTerminalEvidence,
) -> None:
    ...
```

[推測] `_require_handle(observation, CapturedObservation)` (`:280-316`) と `_require_sealed_terminal_evidence(evidence)` の両方を最初に実行する。

[推測] `_assert_observation_row():2510-2533` の slot annotationは `S8BAttemptSlot | S8BV2AttemptSlot` に広げるが、実行時 identity照合はそのままにする。

[推測] `_reject_legacy_v2_terminal():2536-2541` は削除しない。旧 `record_attempt_terminal()` と `record_classified_failure_terminal()` は v1だけを受理し、v2では同じ `[s8b-v2-terminal]` 署名で拒否する。

[推測] `record_sealed_classified_failure_terminal()` は作らない。launcher は pre-probe failureも `begin_classified_failure_observation()` (`:2495-2507`) で observation unionへ閉じる。

[推測] core `record_attempt_terminal():1971-2054` へ `terminal_evidence_sha256: str | None = None` を足す。v1 event keyに fieldが無ければrowへ載せず、v2 keyに存在する場合は non-null digestを必須にする。

## 4. v2 terminal row と replay

[推測] `_S8B_V2_EVENT_KEYS` (`s8b_attempt_profile.py:490-493`) は全 eventへ `measurement_ordinal` を足したうえで、terminalだけへ `terminal_evidence_sha256` を足す。v1 `_S8B_EVENT_KEYS["terminal"]` (`:445-463`) は変更しない。

[推測] core `_parse_row():979-1018` で `terminal_evidence_sha256` が expected keysにある場合だけ exact digest検査する。

[推測] `_reject_unsealed_s8b_v2_terminal():556-563` は `_validate_s8b_v2_terminal_row()` へ置換し、row-localに次を要求する。

- [推測] `terminal_status` は `observed` または `retryable-failure`。
- [推測] evidence digestは non-null。
- [推測] reason/null matrixは E2 setと一致。
- [推測] classification echoは null、`competing_process`、`launch_failure` のいずれか。

[推測] artifact bytesを読む完全検査は adapter の `_assert_terminal_evidence_artifacts()` に置く。core validatorがrowしか受けない現状を偽って「core replayだけでartifact検証済み」と書かない。

[推測] `_replay_current_v2_attempt_registry():857-982` は shared lockをpayload readだけで解放せず、core replayとevidence file readまで同じ `_locked_readonly` 区間へ入れる。

[推測] `_atomic_update_locked():1666-1736` は既存rowsのartifactをtransition前に検査し、新 terminal candidateは `prepare()` がevidenceを公開した後、registry staging前に再検査する。

[推測] `_load_other_generation_budget_counts_locked():1623-1653`、`read_attempt_registry():1862-1885`、`resume_attempt():2791` もv2 terminalがあればartifact検査を通す。

## 5. E2 と genesis bytes

[推測] `S8B_V2_RETRYABLE_FAILURE_REASONS` (`s8b_attempt_profile.py:533`) を次の exact frozensetへ変更する。

```python
frozenset({
    "measurement_environment_conflict",
    "measurement_execution_unavailable",
    "measurement_sample_incomplete",
    "measurement_dispersion_exceeded",
})
```

[実測] genesis は `retryable_failure_reasons` を持つ (`_S8B_GENESIS_KEYS:393-401`) ため、新しく作るv2 genesis bytesとchain headは変わる。

[実測] worktree内の `floor-attempt-registries/*/*/registry.jsonl` は実在0件、tracked 0件である。

[実測]空集合を直接 pinする既存 nodeは `test_v2_profile_is_additive_empty_retryable_and_budgeted_by_cell` の1件 (`test_attempt_registry_core_s8b_profile.py:2172-2216`)。他のv2 fixtureはprofileからgenesisを動的生成するため固定bytes pinではない。

## 6. C2 境界

[推測] C2 は `FloorAttemptReservation` に normalized protocol、mode、perf receipt、v2 slot identity、consumption markerを用意する。launcherへ `expected_use_perf`、`reps_expected`、`session_cv_max` を別引数では渡さない。

[推測] C2 の `terminal_builder(opened)` は次の契約を満たす。

- [推測] `campaign_record` は `_finish_session()` が現在emitする exact session mapping。
- [推測] `raw_output_bytes == serialize_session_line(campaign_record)`。
- [推測] `terminal_status` は campaign self-report。
- [推測] `report_sha256 == sha256(raw_output_bytes)`。
- [推測] `observation_sha256` は observed 時の private repetition evidence digest、それ以外 null。
- [推測] `primary_value` は observed 時の median、それ以外 null。
- [推測] `finished_at` は session外の認証済み terminal timestamp。

[推測] producer capture の既存入口は `capture_attempt_registry_prefix(repo_root, *, expected_binding) -> dict[str, object]` (`s8b_attempt_registry.py:985-1009`) のまま固定する。C1では campaign caller、coverage、`assemble_result`、`RESULT_SCHEMA` v5切替、pending/resumeを実装しない。

## 7. 赤になる既存 test

### 直接赤

- [実測] launcher ordering 3 node (`test_s8b_floor_attempt_launcher.py:268`) は pre-probe追加と capture skipでevent列が変わる。
- [実測] open error 1 node (`:362`) は pre/post probeとprivate sinkの追加でevent列が変わる。
- [実測] 上記4 nodeの `_RecorderRegistry` は `record_sealed_attempt_terminal` を持たないため更新が必要。
- [実測] 同4 nodeの current `raw_output_bytes` と `campaign_record` は一致しない (`:294-315`, `:383-391`) ため、新しい exact bytes gateで赤になる。
- [実測] v2 retryable empty pin 1 node (`test_attempt_registry_core_s8b_profile.py:2172`) はE2で赤になる。
- [実測] blanket terminal validator pin 1 node (`:2251`) は新validatorへ置換されるため赤になる。

### fixture 経由の transitive 赤

- [実測] `_reservation()` (`test_s8b_floor_attempt_launcher.py:192-211`) に必須 fieldを足すため、このhelperを使う11 nodeがconstructor errorになる。
- [実測] real genesis test (`:510-597`) も `FloorAttemptReservation` を直接組むため、launcher fileの全12 nodeがfixture更新対象になる。
- [実測] v2 historical terminalを `terminal_evidence_sha256` 無しで作る `test_terminal_validator...` (`:2273-2297`) はcore exact key経路でも赤になる。

### supersede 可

- [実測] A2α 14節の core pin `test_terminal_validator_direct_replay_and_producer_mapping_keep_v1_positive` はv2部分だけsupersedeする。v1正例と下層validator直呼びは維持する。
- [実測] adapter pin `test_v2_marker_claim_v3_resume_and_legacy_terminal_fail_closed` は「v2 terminal全拒否」から「旧APIは拒否、sealed APIは受理」へ更新する。
- [実測] `S8B_V2_RETRYABLE_FAILURE_REASONS == frozenset()` の assertionはsupersedeする。

### supersede 禁止

- [実測] v1 `S8B_RETRYABLE_FAILURE_REASONS` の空集合 pin (`test_attempt_registry_core_s8b_profile.py:296-328,792-803,2213-2216`)。
- [実測] adapterのv1 terminal 12 nodeとcore/S8C/equivalence/trialの28 node。
- [実測] B2/D1 のprefix proof 19 node、prefix inspector 22 node。
- [実測] `RESULT_SCHEMA == v4` とv4 result consumer pin。
- [実測] caller指定 `rep_observations` を拒否するnode (`test_s8b_floor_attempt_launcher.py:609` の4 param中1件)。
- [実測] spawn-site pinは同じ `_owned_post_probe` を使う限りsupersedeしない。

## 8. test 計画

[推測] 新規 test fileは作らず、次へ追加する。

### `test_s8b_floor_attempt_launcher.py`

- [推測] pre-probe competitionで `capture` とpost-probeを呼ばず、reserve/classify/build/observe/sealed terminalへ進む正例。
- [推測] pre noncompeting、post competing、launch failure、no failureのprecedence 4 param。
- [推測] private sinkが `token.open()` 内でだけ更新され、snapshotがopen後になる直接node。
- [推測] callerの `rep_observations` 指定が従来どおり副作用前に拒否される対照。
- [推測] `probe_after=None` かつthroughputs有りをevidence sealが拒否するnode。
- [推測] protocol、receipt、campaign_record内のnested callableをseal前に拒否するnode。
- [推測] forged `SealedTerminalEvidence` とseal差替えを拒否するnode。

### `test_attempt_registry_core_s8b_profile.py`

- [推測] v2 terminal keyだけが `terminal_evidence_sha256` を持ち、v1 key集合が不変である直接node。
- [推測] E2 exact 4語と genesis projectionを固定するnode。
- [推測] v2 equality policyはfalse、echo equalityはcoreで維持されるnode。
- [推測] row-local validatorを直接呼び、digest欠落、E2外reason、`terminal-failure`、`not-consumed` を個別拒否する4 param。
- [推測] lower validatorを直接spyして実効発火を固定するD1522 node。

### `test_s8b_attempt_registry.py`

- [推測] launcher経由でv2 terminalを書き、evidence file実在、digest一致、read replay成功を検査する5 param正例: observed + E2 4語。
- [推測] `self_report` の status、excluded reason、primaryを各1箇所だけ変える3 param負例。
- [推測] evidence file欠落、bytes改竄、row digest差替えの3 node。
- [推測] 旧 `record_attempt_terminal` でv2を閉じるnode。
- [推測] evidence fileを実際に読んだことを `_read_regular_bytes` spyで固定するD1522 node。
- [推測] classification raw reason、external evidence digest、terminal E2 reasonの三者方向を直接検査するnode。
- [推測] raw output digest、report digest、observation digestをそれぞれ1箇所だけ変える3 node。
- [推測] terminal rowあり、evidenceなしのreplayを拒否するnode。
- [推測] evidenceあり、terminal rowなしのorphanは現registryを壊さない正例。

[推測] 各負例はpure evidence projector、profile validator、adapter artifact helper、launcher recorder fakeのいずれかを直接呼び、上流の別gateに遮られない観測nodeにする。integration nodeだけで下層を代用しない。

## 9. 所有分割

[推測] C1a は1実装子で次を所有する。

```text
orchestrator/campaign/s8b_floor_attempt_launcher.py
orchestrator/tests/test_s8b_floor_attempt_launcher.py
```

[推測] C1b は境界を固定後、2実装子で並列化できる。

```text
unit1:
  orchestrator/campaign/s8b_terminal_evidence.py
  orchestrator/campaign/s8b_floor_attempt_launcher.py
  orchestrator/tests/test_s8b_floor_attempt_launcher.py

unit2:
  orchestrator/campaign/attempt_registry_core.py
  orchestrator/campaign/s8b_attempt_profile.py
  orchestrator/campaign/s8b_attempt_registry.py
  orchestrator/tests/test_attempt_registry_core_s8b_profile.py
  orchestrator/tests/test_s8b_attempt_registry.py
```

[推測] unit1/unit2の共有境界は `SealedTerminalEvidence` の3 private field、`record_sealed_attempt_terminal(observation,evidence) -> None`、19 field document、`TerminalProjection` のstatus/reason/digest/primary/finished/campaign recordで固定する。file所有は重ならない。

# 4. 変異事前登録の候補

| ID | 変異位置と内容 | KILLED 期待 node | 他 gateに遮られない理由 |
|---|---|---|---|
| M1 | [推測] 新 `s8b_terminal_evidence.py` のprojectionで再導出reasonを `self_report.excluded_reason` のコピーへ置換 | `test_terminal_evidence_rejects_each_self_report_mismatch[excluded-reason]` | [推測] projector直接呼びでadapter/coreを通さず、raw factsだけを固定する。 |
| M2 | [推測] `s8b_attempt_profile.py:533` のE2から `measurement_dispersion_exceeded` を1語落とす | `test_s8b_v2_retryable_reason_vocabulary_is_exact[measurement-dispersion-exceeded]` | [推測] profile set直接検査でnull matrixへ到達させない。 |
| M3 | [推測] `launcher.py:582-590` のpre-probe競合分岐でcaptureを実行する | `test_pre_probe_competition_terminalizes_without_capture` | [推測] recorder fakeがcapture callそのものを観測する。 |
| M4 | [推測] `s8b_attempt_registry.py:857-982` のartifact replayをdigest文字列比較だけにしfileを読まない | `test_terminal_artifact_reader_is_invoked_before_replay_accepts` | [推測] core-valid rowと実在fileを用意し、reader spyのcall数だけを見る。 |
| M5 | [推測] `launcher.py:616-628` でprivate sink snapshotを`token.open()`前へ移す | `test_private_rep_sink_snapshot_occurs_after_token_open` | [推測] fake tokenがopen時にだけsinkへ値を入れる。 |
| M6 | [推測] `perf_preflight.py:261` を使わずcallerの `expected_use_perf` を採る | `test_terminal_evidence_rejects_perf_bool_not_derived_from_receipt` | [推測] receipt自体はvalidで、boolだけを反転するpure seal test。 |
| M7 | [推測] protocol digest equalityを削除し、callerの `session_cv_max` を採る | `test_terminal_evidence_rejects_protocol_policy_not_bound_to_registry_generation` | [推測] evidence shapeとthroughputsはvalidにし、protocol digestだけを別値にする。 |
| M8 | [推測] projectionの `open_failure` 分岐を削除 | `test_sealed_terminal_projection_maps_open_failure_to_execution_unavailable` | [推測] probe、launch failures、rep evidenceを中立にし、open failureだけを発火させる。 |
| M9 | [推測] `s8b_attempt_profile.py:662-673` のv2 equality flagをtrueへ戻す | `test_sealed_terminal_positive[measurement-sample-incomplete]` | [推測] classification reasonはnull、evidence E2 reasonはsampleで、他の全artifactはvalid。 |
| M10 | [推測] `_S8B_V2_EVENT_KEYS:490-493` から `terminal_evidence_sha256` を除く | `test_v2_terminal_event_keys_add_only_terminal_evidence_digest` | [推測] schema table直接検査。 |
| M11 | [推測] raw digestを `campaign_record` serializationでなくterminal builder申告からコピーする | `test_terminal_evidence_rejects_raw_output_campaign_record_mismatch` | [推測] builderのraw bytesとrecordだけを違わせ、seal直接で観測する。 |
| M12 | [推測] `_reject_legacy_v2_terminal():2536-2541` を削除 | `test_legacy_terminal_api_rejects_v2_before_calling_core` | [推測] core terminalをsuccess spyへ差替え、旧APIが下層へ到達したこと自体を失敗にする。 |
| M13 | [推測] sealed APIのexact type/seal identity検査をtruthy検査へ緩和 | `test_record_sealed_terminal_rejects_forged_process_local_seal` | [推測] document、digest、rowはvalidにし、sealだけを差し替える。 |
| M14 | [推測] `probe_after=None` をpre-probe非競合またはthroughputs有りでも許す | `test_terminal_evidence_rejects_probe_after_absent_with_measurement` | [推測] pure document validator直接で、artifact/path gateは通さない。 |
| M15 | [推測] `_atomic_update_locked():1713-1733` の順序をregistry replace後にevidence publishへ逆転 | `test_terminal_publish_fault_never_exposes_row_without_evidence` | [推測] replace直後へfaultを入れ、read replayがmissing artifactを観測する。 |
| M16 | [推測] terminal precedenceでrep integrity/sampleよりdispersionを先にする | `test_sealed_terminal_precedence_rep_integrity_precedes_dispersion` | [推測] CV超過throughputsとrep failureを同居させ、environment/open failureは中立にする。 |

## 総括

- [実測] 親案の14 fieldは不足し、5 field追加の19 field契約を採る。
- [推測] 追加は `protocol`、`perf_preflight_receipt`、`open_failure`、`campaign_record`、`finished_at`。
- [推測] (P1) C1/C2分割は採用し、C1をさらにC1a/C1bへ分ける。
- [推測] (P2) launcher所有pre-probeを採用する。
- [推測] (P3) evidence-bound handleを採用する。
- [推測] (P4) 理由ありは `retryable-failure`、理由なしは `observed` を採用する。
- [推測] v2のclassification文字列等値は外し、adapterのraw-facts再導出へ置換する。
- [推測] (P5) 1 wave実装は不採用。
- [推測] (P6) receipts dirへのcreate-only公開とrow digest束縛を採用する。
- [推測] 実装子はC1a 1本、C1b 2本、合計3本。
- [推測] 規模はproduction約730-1,040 touched行、test込み約1,600-2,300 changed LOC。
- [実測] pytest未実走であり、緑は主張しない。