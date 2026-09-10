# 依頼 1 — 規模の実測と分割判定

## 前提

- [実測] HEAD は指定どおり `50dbf91581cfb5c7f59eb1eac21815b5cdab5c15`、worktree は clean だった。
- [実測] sandbox は read-only であり、pytest は実行していない。以下の node 数は test AST、`pytest.mark.parametrize` の列挙値、直接参照を静的に数えた結果である。
- [実測] 本 scope で変更する production file は 4 file、既存 test file は 4 fileである。単位 C / D2 の file は変更対象に含めない。

## production 変更面と規模

| 群 | production file / 現行アンカー | 変更・新設 symbol | production LOC 見積り |
|---|---|---|---:|
| [推測] B2-a | `s8b_attempt_registry.py:4-8,637-817,1631-1654` | module ownership docstring、`_replay_current_v2_attempt_registry`、`capture_attempt_registry_prefix`、`inspect_attempt_registry_prefix` | 追加 120〜170、変更 4〜8、削除 0 |
| [推測] D1-b | `attempt_registry_core.py:240-266,283-297,423-468` | `ATTEMPT_REGISTRY_PREFIX_PROOF_SCHEMA`、`ATTEMPT_REGISTRY_PREFIX_PROOF_KEYS`、`validate_attempt_registry_prefix_proof` | 追加 50〜75、変更 0〜4、削除 0 |
| [推測] D1-a | `s8b_floor_contract.py:29-38,81-87,157-166` | `LEGACY_RESULT_SCHEMA`、現行 `RESULT_SCHEMA`、`RESULT_SCHEMA_V5`、`READABLE_RESULT_SCHEMAS`、`_RESULT_V4_KEYS`、`_RESULT_V5_KEYS`、`_RESULT_KEYS_BY_SCHEMA`、`result_keys_for_mode` | 追加 25〜40、変更 10〜20、削除 0〜5 |
| [推測] D1-c | `s8b_floor_stats.py:682-768` | `verify_floor_artifact` の schema dispatch、proof validation、独立 proof 比較。signature に `expected_attempt_registry` を追加 | 追加 45〜75、変更 10〜20、削除 0〜5 |
| [推測] D1-d | `s8b_floor_stats.py:1036-1082` | `verify_floor_artifact_with_live_admission` の v5-only inspection 分岐、expected binding 導出 | 追加 45〜65、変更 5〜10、削除 0〜5 |
| [推測] 合計 | 4 production file | 既存 3 関数変更、新設 3 関数と定数群 | 追加 285〜425、変更 29〜62、削除 0〜15、changed LOC 約 314〜502 |

- [実測] B2-a は `_registry_generation_paths_locked` 76 行、`_profile_and_binding_for_generation` 91 行、`read_attempt_registry` 24 行を再利用できるため、これらを複製する見積りではない。`s8b_attempt_registry.py:649-817,1631-1654`
- [実測] D1-c は 352 行ある verifier 全体を書き換えず、現行の schema/key/admission 前段約 87 行へ分岐を追加する。`s8b_floor_stats.py:682-768`
- [推測] test 実装は追加 420〜650 行、変更 20〜40 行程度で、production と合わせた総 changed LOC は約 750〜1,190 行である。A1' / A2α の下振れ実績を考慮した上限である。

## `result_keys_for_mode` と `RESULT_SCHEMA` の実数

### `result_keys_for_mode`

- [実測] 親 brief の「22 呼出し、production 4 file / test 3 file」は現 HEAD と一致しない。
- [実測] syntactic call expression は合計 12 件である。production 3 件、test 9 件である。

| 区分 | 現物 |
|---|---|
| [実測] production 3 call | `s8b_floor_stats.py:734`、`s8b_holdout_freeze.py:1429`、`s8b_ratified_freeze.py:2360` |
| [実測] test 9 call | `test_s8b_floor_campaign.py:1297,7049`、`test_s8b_floor_contract.py:368,369,370,376,381`、`test_s8b_ratified_freeze.py:1469,1616` |
| [実測] call ではない参照 | `test_official_perf_closure.py:36,205,209,223` は文字列による AST inventory であり、呼出し式ではない |

### `RESULT_SCHEMA`

- [実測] raw word search では production 7 file、test 5 fileである。
- [実測] 親 brief の production 6 file は定義元 `s8b_floor_contract.py` を除いた数であるが、うち `paper_story_a1_paired.py` と `s8b_oracle_n_pilot.py` は別成果物の同名ローカル定数であり、S8B floor result の参照ではない。
- [実測] S8B floor result の意味的な production 閉包は、定義元を含めて 5 file、参照側だけなら 4 fileである。

| 区分 | file |
|---|---|
| [実測] S8B production | `s8b_floor_contract.py`、`s8b_floor_campaign.py`、`s8b_floor_stats.py`、`s8b_holdout_freeze.py`、`s8b_ratified_freeze.py` |
| [実測] production の同名衝突 | `paper_story_a1_paired.py`、`s8b_oracle_n_pilot.py` |
| [実測] S8B test/support | `s8b_v2_freeze_fixture.py`、`test_s8b_floor_campaign.py`、`test_s8b_floor_contract.py`、`test_s8b_ratified_verify.py` |
| [実測] test の同名衝突 | `test_codex_role_runtime.py` のローカル JSON schema |

## test node の実数

| 群 | 更新 node | 新設 node | 既存の直接参照・回帰 node |
|---|---:|---:|---:|
| [推測] B2-a | 0 | 13 | 既存 helper 回帰 8 |
| [推測] D1-b | 0 | 16 | 新 symbol なので 0 |
| [推測] D1-a | 2 | 0 | 7 |
| [推測] D1-c / D1-d | 0 | 9 | 69 |
| [推測] 合計 | 2 | 38 | unique 84。ただし更新対象は 40 nodeだけ |

### B2-a が再利用する既存 helper の 8 node

- [実測] `test_s8b_attempt_registry.py::test_canonical_v1_lifecycle_ignores_non_generation_sibling`
- [実測] `::test_generation_enumerator_rejects_unsafe_hex_authority_and_accepts_real_one` の 4 parameter node
- [実測] `::test_complete_generation_directory_symlink_is_rejected_but_real_directory_mutates`
- [実測] `::test_unchecked_generation_symlink_would_double_count_one_registry_budget`
- [実測] `::test_generation_resolver_accepts_canonical_v1_current_authority`

### D1-a の 7 参照 node

- [実測] `test_s8b_floor_contract.py::test_floor_campaign_directly_reexports_shared_leaf_objects`
- [実測] `test_s8b_floor_contract.py::test_result_v4_key_contract_is_mode_conditional_and_exact`
- [実測] `test_s8b_floor_campaign.py::test_perf_preflight_journal_record_is_outside_certified_artifacts`
- [実測] `test_s8b_floor_campaign.py::test_official_degraded_result_records_strict_perf_observation`
- [実測] `test_s8b_ratified_freeze.py::test_happy_path_resolves_and_loads`
- [実測] `test_s8b_ratified_freeze.py::test_degraded_result_observation_is_exactly_bound_to_manifest`
- [実測] `test_official_perf_closure.py::test_official_perf_surface_inventory_is_exact`

### D1-c / D1-d の 69 参照 node

- [実測] `test_s8b_floor_stats.py` 内は 51 test function、parametrize 展開後 58 nodeである。
- [実測] その 58 node は `test_verify_accepts_consistent_artifact`、`test_pilot_degraded_preserves_legacy_shape_without_perf_observation`、`test_official_degraded_requires_and_consumes_perf_observation`、`test_official_degraded_keeps_all_five_internal_consistency_conditions`、`test_official_perf_present_keeps_legacy_exact_shape`、`test_expected_use_perf_cannot_disagree_with_artifact_receipt`、`test_degraded_floor_stats_require_consumed_throughput_claim`、`test_degraded_floor_stats_bind_run_cmd_from_same_result`、`test_degraded_floor_stats_bind_raw_counters_from_same_result`、`test_verify_requires_expected_use_perf_keyword_argument`、`test_verify_requires_expected_holdout_admission_keyword_argument`、`test_live_verifier_signature_forbids_caller_supplied_expected_admission`、`test_live_refreeze_comparison_is_centralized_once_and_has_three_callers`、`test_live_verifier_rejects_both_refreeze_mismatch_directions` 2 node、`test_live_verifier_rejects_result_v4_unexpected_top_level_key`、および `test_verify_rejects_*` / `test_verify_detects_*` / `test_verify_accepts_zero_perf_counters` の `:960-1325` にある 36 functionである。
- [実測] `:960-1325` の parametrize 増分は `test_verify_rejects_exempt_session_exclusion_class_tamper` 2、`test_verify_rejects_normalizable_session_scalar_types` 4、`test_verify_rejects_bool_in_rep_observation` 2、`test_verify_rejects_unknown_or_missing_rep_evidence` 2 nodeである。
- [実測] 外部の 10 nodeは、`test_s8b_floor_campaign.py::test_two_phase_finalize_crash_injection_recovers_at_all_four_boundaries` 4 node、`::test_end_to_end_golden_floor_values_and_tamper_detection`、`::test_real_seal_protocol_to_floor_official_core_e2e`、`::test_verify_floor_artifact_binaries_positive_and_negative`、`test_s8b_holdout_admission.py::test_official_fresh_v2_marker_alone_disqualifies_and_live_mismatch_is_exact`、`test_s8b_holdout_freeze.py::test_v2_candidate_threads_receipt_derived_degraded_mode_to_floor_stats`、`test_s8b_ratified_freeze.py::test_degraded_launch_threads_expected_use_perf_to_every_consumer` である。
- [実測] 残る 1 node は `test_official_perf_closure.py::test_official_perf_surface_inventory_is_exact` である。

## 単独実装時の整合性

| 群 | 単独で production 整合・既存 test green を維持できるか |
|---|---|
| [実測] D1-b | できる。新 validator と定数だけの加法変更で既存 core API を変えない |
| [推測] B2-a | D1-b の proof validatorと定数を使うため、B2-a単独では不可。D1-bと束ねる |
| [推測] D1-a | できる。`RESULT_SCHEMA` は v4のまま、`schema` defaultもv4なので全既存 callが互換 |
| [推測] D1-c | 単独では不可。D1-aの schema/key集合とD1-bの validatorが必要 |
| [推測] D1-d | 単独では不可。B2-aの inspection APIとD1-cの新 kw-only引数が必要 |
| [推測] 最小の安定 checkpoint | 前半 `D1-b + B2-a`、後半 `D1-a + D1-c + D1-d`。前半だけでも productionは整合し、既存 v4 testは不変 |

## 分割判定

- [推測] **1 wave、実装子2本、fix 3巡以内で安全に扱える。wave自体は分割しない。**
- [推測] 実装子1は `attempt_registry_core.py`、`s8b_attempt_registry.py` と対応testを所有し、内部順を D1-b → B2-a とする。
- [推測] 実装子2は `s8b_floor_contract.py`、`s8b_floor_stats.py` と対応testを所有し、実装子1の公開signature確定後に D1-a → D1-c → D1-d を行う。
- [推測] file所有は完全に素であり、最終的に1 commitへ統合できる。
- [推測] 予備のwave分割が必要になった場合も境界は同じ前半/後半に限定するが、現実測規模では分割条件に達しない。

# 依頼 2 — 実装プラン

## 1. B2-a read-only prefix inspector

### 配置と import 判定

- [実測] `s8b_attempt_registry.py` は既に `s8b_holdout_admission` を importしている。`s8b_attempt_registry.py:32-35`
- [実測] 逆向きに `s8b_holdout_admission.py` から adapterを importすると循環するうえ、`test_s8b_attempt_registry.py:1729-1775` の直接import禁止meta-testに違反する。
- [実測] `s8b_floor_stats.py` は admission → ratified → stats のimport鎖に入るため、adapterのtop-level importは避け、live wrapper内の局所importにする必要がある。`s8b_holdout_admission.py:40-45`、`s8b_ratified_freeze.py:44-48`
- [実測] よって (P2) の「公開APIを `s8b_attempt_registry` に置く」は採用するが、「admissionが呼ぶ」は却下する。呼び手は単位Cのlauncher wrapperとD1-dのstats局所importに限定する。

### 固定する signature

- [推測] D1-bを先に置いた上で、`s8b_attempt_registry.py:817` の直後に次を置く。

```python
def capture_attempt_registry_prefix(
    repo_root: Path,
    *,
    expected_binding: profile8b.S8BAttemptBinding,
) -> dict[str, object]:
    ...

def inspect_attempt_registry_prefix(
    repo_root: Path,
    *,
    expected_binding: profile8b.S8BAttemptBinding,
    row_count: int,
    chain_head_sha256: str,
) -> dict[str, object]:
    ...
```

- [推測] 両関数の戻り値は次のexact 7 keyで固定する。producer captureはlive tailのN/head、verifier inspectionは報告されたN/headを再現した独立proofを返す。

```python
{
    "schema": "s8b-floor-attempt-registry-proof/v1",
    "registry_schema": "s8b-floor-attempt-registry/v2",
    "freeze_sha256": str,
    "protocol_sha256": str,
    "schedule_sha256": str,
    "row_count": int,
    "chain_head_sha256": str,
}
```

### lock と replay

- [実測] `read_attempt_registry()` は排他write lockである `admission._locked(root)` を使う。`s8b_attempt_registry.py:1631-1654`
- [実測] `_locked_readonly(root)` は既存lock inodeを変更せず `O_RDONLY | O_NOFOLLOW` と `LOCK_SH` を使い、`category/reason` を持つ `FloorHoldoutEvidenceError` を返す。`s8b_holdout_admission.py:186-201,730-755`
- [推測] B2-aは `_locked_readonly(root)` を選ぶ。証拠取得はread-onlyであり、write lockを使うとread-only APIの契約と並行reader性を不必要に弱める。
- [推測] lock区間内で `_registry_generation_paths_locked(root, freeze)` → expected protocol pathの一意選択 → `_read_regular_bytes` → `_peek_registry_genesis` → `_profile_and_binding_for_generation` → `core.load_attempt_registry` の順に実行する。`s8b_attempt_registry.py:582-817`
- [実測] `_profile_and_binding_for_generation` はgenesisからbinding、budget、schemaを読み、現行scheduler authorityを使って世代固有profileを構築し、path、recovery policy、genesis replayを検査する。`s8b_attempt_registry.py:727-817`
- [推測] proof対象はgenesisの `schema_version == S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION` かつ2段pathのものだけとする。canonical 1段v1と、2段pathに置かれた合成v1は対象外にする。
- [実測] 1段v1を除外する根拠はD1194の前向き適用と、v5 proofの `registry_schema` がv2で固定されることである。既存v1 reader/recoveryは変更しない。

### 構造化拒否

- [実測] 現物には親依頼がいう `_fail(category, reason)` helperはなく、構造化された実体は `FloorHoldoutEvidenceError(category=..., reason=...)` である。`s8b_holdout_admission.py:186-201`
- [推測] B2-aはこの実体へ揃え、lock側の同例外はそのまま通し、adapter/core例外を次へ写す。

| category | reason |
|---|---|
| [推測] `unverifiable` | `attempt-registry-path-unavailable`、`attempt-registry-read-unavailable` |
| [推測] `mismatch` | `attempt-registry-generation-unsupported`、`attempt-registry-binding-mismatch`、`attempt-registry-replay-invalid`、`attempt-registry-proof-invalid` |
| [推測] `mismatch` | `attempt-registry-prefix-too-short`、`attempt-registry-prefix-head-mismatch` |

## 2. verifier inspection の意味論

- [推測] `inspect_attempt_registry_prefix` はrow_count/headの型検査後も、先にlive file全体を `core.load_attempt_registry(data, profile=..., expected_binding=...)` へ渡す。
- [推測] full replayが成功した後だけ、順に `len(rows) >= row_count`、`rows[row_count - 1]["event_sha256"] == chain_head_sha256` を検査する。
- [推測] `rows[-1]` との比較は禁止する。正当なappend後もN行目は変わらないため受理する。
- [推測] N以後のinvalid JSON、noncanonical row、event index破壊、previous hash切断、event hash不一致はprefix比較前のfull replayで拒否する。
- [推測] verifier戻り値の `row_count` と `chain_head_sha256` は報告値を保持し、live tailの長さ/headへ更新しない。

## 3. D1-b proof object

- [推測] `attempt_registry_core.py:266` の直後、chain primitiveの近傍へ次を置く。

```python
ATTEMPT_REGISTRY_PREFIX_PROOF_SCHEMA = (
    "s8b-floor-attempt-registry-proof/v1"
)
ATTEMPT_REGISTRY_PREFIX_PROOF_KEYS = frozenset({
    "schema",
    "registry_schema",
    "freeze_sha256",
    "protocol_sha256",
    "schedule_sha256",
    "row_count",
    "chain_head_sha256",
})

def validate_attempt_registry_prefix_proof(
    value: object,
) -> dict[str, object]:
    ...
```

- [推測] `value` はMappingかつexact 7 key、`schema` はproof/v1 literal、`registry_schema` はbounded nonempty string、4 digestはlowercase hex64、`row_count` はboolを除く正整数、headはzero SHAではないことを検査する。
- [推測] validatorはfreshなplain dictを固定順で返す。
- [実測] `_digest` はlowercase hex64を既に検査できる。`attempt_registry_core.py:283-288`
- [推測] `chain_head_sha256 == rows[N-1]["event_sha256"]` はvalidator単体の保証にしない。validatorはshape/typeだけ、等値の実体はB2-aのfull replay後のprefix比較だけが保証する。

## 4. D1-a result契約

- [実測] 現producerは `s8b_floor_campaign.RESULT_SCHEMA` をcontractからreexportし、`assemble_result()` がその値を書いている。`s8b_floor_campaign.py:169,6703-6706,6813-6815`
- [実測] したがって `RESULT_SCHEMA` をv5へ変えるとproofを持たない現producerが壊れるため、(P1)を採用する。
- [推測] `s8b_floor_contract.py:29-38,81-87` を次の構造にする。

```python
LEGACY_RESULT_SCHEMA = "s8b-floor-result/v4"
RESULT_SCHEMA = LEGACY_RESULT_SCHEMA
RESULT_SCHEMA_V5 = "s8b-floor-result/v5"
READABLE_RESULT_SCHEMAS = frozenset({
    LEGACY_RESULT_SCHEMA,
    RESULT_SCHEMA_V5,
})

_RESULT_V4_KEYS = frozenset({...existing keys...})
_RESULT_KEYS = _RESULT_V4_KEYS
_RESULT_V5_KEYS = _RESULT_V4_KEYS | {"attempt_registry"}
_RESULT_KEYS_BY_SCHEMA = {
    LEGACY_RESULT_SCHEMA: _RESULT_V4_KEYS,
    RESULT_SCHEMA_V5: _RESULT_V5_KEYS,
}
```

- [推測] `_RESULT_KEYS` は既存private testとconsumer互換のためv4 aliasとして保存する。
- [推測] `result_keys_for_mode` は次で固定する。

```python
def result_keys_for_mode(
    mode: object,
    *,
    schema: object = LEGACY_RESULT_SCHEMA,
    perf_preflight: object | None = None,
) -> frozenset[str]:
    ...
```

- [実測] schema defaultをv4にすればproduction 3 callとtest 9 callを変更せず、D2所有のholdout/ratified fileにも触れないため、(P4)を採用する。
- [実測] `test_s8b_floor_contract.py:180` の `RESULT_SCHEMA == v4`、`test_s8b_floor_stats.py:596` のhonest fixture、`:1323-1325` のv3拒否とv4 error pinは変更しない。

## 5. D1-c / D1-d verifier

### pure verifier

- [推測] `verify_floor_artifact()` のsignatureだけ次へ拡張する。

```python
def verify_floor_artifact(
    artifact: Mapping,
    expected_protocol: Mapping,
    expected_binaries: Optional[Mapping] = None,
    *,
    expected_holdout_admission: Mapping,
    expected_use_perf: bool,
    expected_attempt_registry: Mapping[str, object] | None = None,
) -> list:
    ...
```

- [推測] v4は従来のkey集合を使うため、top-level `attempt_registry` はexact key検査のextra key経路で拒否する。
- [推測] v3等の非readable schemaは、現行testのerror bytesを守るため、v4 key集合検査後に既存の `"artifact.schema が 's8b-floor-result/v4' でない"` を返す。
- [推測] v5はtop-level exact keyでproofを必須化し、D1-b validator、`registry_schema == v2`、正のN、nonzero headを検査する。
- [推測] `expected_attempt_registry` も同validatorへ通し、比較方向を `reported_proof == independently_replayed_live_prefix` に固定する。報告値を期待値へ流用しない。
- [推測] v4で `expected_attempt_registry` が非Noneならcaller契約違反として拒否し、v4のartifact受理判定にregistryを混ぜない。

### live wrapper

- [推測] `verify_floor_artifact_with_live_admission()` は既存signatureを維持する。`s8b_floor_stats.py:1036-1044`
- [推測] artifact schemaがv5のときだけ局所importしたB2-a APIを呼ぶ。v4、v3、欠損schemaではattempt registryを読まない。
- [推測] expected bindingは既存引数だけから次のように導出する。

| field | 出所 |
|---|---|
| [実測] `freeze_sha256` | wrapperの既存必須引数 `freeze_sha256`。`:1040` |
| [実測] `protocol_sha256` | `s8b_floor_contract.canonical_protocol_sha256(protocol)`。contract `:552-564` |
| [実測] `schedule_sha256` | `sha256(core.canonical_json_bytes(list(schedule)))`。既存admissionも同じcanonical list digestを用いる。`s8b_holdout_admission.py:5614-5616` |

- [推測] wrapperはreported proofをD1-bでshape検査してN/headだけをB2-aへ渡し、B2-aから返った独立proofをpure verifierの `expected_attempt_registry` へ渡す。
- [推測] reported proofのfreeze/protocol/scheduleをpath選択に使用しない。別binding proofでも、外部引数が選んだ正しいregistryを検査した後、pure verifierの全7 field比較で拒否する。

## 6. 今回は実装しない境界

### coverage

- [推測] D2で追加するsymbolと型境界を次で固定する。

```python
AttemptIdentity = tuple[str, str, str, str]
# (campaign_run_id, manifest_sha256, run_relpath, attempt_id)

def validate_attempt_registry_prefix_coverage(
    *,
    prefix_rows: Sequence[Mapping[str, Any]],
    row_count: int,
    result_attempt_identities: Sequence[AttemptIdentity],
    authoritative_attempt_identities: Sequence[AttemptIdentity],
) -> None:
    ...
```

- [推測] D2は各Sequenceで重複を先に拒否し、result attempts、`prefix_rows[:row_count]` 内のsealed terminal、schedule/admissionから独立導出したauthoritative集合の三者を全単射で照合する。
- [実測] producer由来の二集合だけではB2-1/A2-6を閉じないため、authoritative集合を第三引数として残す。
- [推測] 本waveではsymbolを実装せず、signatureだけをこのplanで固定する。

### 単位Cからのproducer capture

- [推測] 単位Cはcampaignからadapterを直接importせず、launcherに次のthin wrapperを設ける。

```python
def capture_floor_attempt_registry_prefix(
    *,
    repo_root: Path,
    binding: object,
) -> Mapping[str, object]:
    ...
```

- [推測] fresh経路は全attempt終了とholdout admission inspection後、`assemble_result()` 前に一度だけcaptureし、Cが拡張する `assemble_result(..., attempt_registry=proof)` へ渡す。`s8b_floor_campaign.py:7935-7963`
- [推測] `M-finalize-pending` はpending result内のproofを再読し、live inspectionするだけで、新しいtailからNをcaptureし直さない。`s8b_floor_campaign.py:7790-7833`
- [推測] `attempts[*].attempt_id` の追加はC/D2まで行わない。

### `finished_at`

- [実測] `finished_at` は既にregistry terminalの認証対象fieldであり、coreが型検査してrowへ格納する。`attempt_registry_core.py:1890-1918,1946-1957`
- [実測] adapterとlauncherの引数にも既に存在する。`s8b_attempt_registry.py:2320,2379`、`s8b_floor_attempt_launcher.py:126-141,637-644`
- [推測] B2-8に従いsession recordへは追加しない。Cがsealed terminalを開くときもregistry terminal fieldのまま使い、journal v3 exact keysを変更しない。

### D2のconsumer 3面

- [推測] 新規candidateのv5-only化は `_validate_floor_inputs()` とそのresult load部で行う。`s8b_holdout_freeze.py:1373,1417-1462,1620`
- [推測] earlier resultのv4/v5分岐とinvalid v5のunderivable化は `_official_earlier_floor_results()` / `_derive_floor_selection_eligibility()` で行う。`s8b_holdout_freeze.py:1813-1925`
- [推測] ratified reverifyのschema別keysとv5 live proof/coverageは `_validate_result_top_level_keys()`、`_validate_result()`、launch validateのwrapper callで行う。`s8b_ratified_freeze.py:2352-2409,3274-3319`
- [推測] 本waveでは上記2 production fileを1 byteも変更しない。

## 7. 赤になる既存testとpin

### 直接赤

- [推測] **0 node。** v4 default、`RESULT_SCHEMA == v4`、既存signatureの必須引数、既存error文字列を保存する設計だからである。
- [推測] `test_s8b_floor_contract.py` の2 nodeは新定数/v5 keyを追加検査するよう拡張するが、旧assertionをsupersedeしない。

### fixture経由のtransitive赤

- [推測] **0 node。** `s8b_v2_freeze_fixture.py:340`、`test_s8b_floor_campaign.py:6552`、`test_s8b_ratified_verify.py:460` は引き続きv4 artifactを生成する。
- [推測] これらをv5へ変えるとproof/live registryを持たないfixture群へ広く波及するため、本waveで変更してはならない。

### supersede判定

- [実測] supersedeしてよい既存pinは無い。
- [実測] supersede禁止は `test_s8b_floor_contract.py:180`、`test_s8b_floor_stats.py:596,1323-1325`、`test_s8b_attempt_registry.py:3000-3167` のv2 terminal二層拒否である。
- [推測] 新しいv5正例・負例は既存v4 pinと並置する。

## 8. テスト計画

### B2-a: `test_s8b_attempt_registry.py` に13 node追加

- [推測] 正例3 node: genesis-only capture、B1 capabilityを消費したgenesis+reservation capture、正当append後のinspection。
- [推測] 負例7 node: N内改竄、N以後invalid JSON、N以後chain切断、N>len、head改竄、1段v1、write lockを呼ぶtripwire付きread-only lock検査。
- [推測] binding負例3 node: freeze/protocol/scheduleの各digest差替え。
- [推測] 各負例はvalid v2 path、valid proof shape、正しい他bindingを維持し、対象のreplay/prefix/binding gate以外では拒否されない形にする。

### D1-b: `test_attempt_registry_core_s8b_profile.py` に16 node追加

- [推測] 正例1、proof field欠落1、余分key1、各7 fieldの型違反7、row_count 0が1、freeze/protocol/schedule/headのhex不正4、zero head 1で計16。
- [推測] core validatorを直接呼ぶため、artifact exact-key、live admission、prefix inspectionには遮られない。D1522の下層直接検査になる。

### D1-a: `test_s8b_floor_contract.py` の既存2 nodeを拡張

- [推測] `test_floor_campaign_directly_reexports_shared_leaf_objects` にv4 current、v5別名、readable集合を追加する。
- [推測] `test_result_v4_key_contract_is_mode_conditional_and_exact` にv5がv4+`attempt_registry`であること、schema defaultがv4であること、未知schema拒否を追加する。
- [推測] 現在のv4 assertionは全部残す。

### D1-c / D1-d: `test_s8b_floor_stats.py` に9 node追加

- [推測] `test_pure_verifier_accepts_v5_with_independent_prefix_proof`
- [推測] `test_pure_verifier_rejects_v4_attempt_registry_as_extra_key`
- [推測] `test_v5_rejects_missing_attempt_registry_proof`
- [推測] `test_v5_rejects_reported_prefix_head_tamper`
- [推測] `test_v5_rejects_proof_binding_mismatch[freeze]`
- [推測] `test_v5_rejects_proof_binding_mismatch[protocol]`
- [推測] `test_v5_rejects_proof_binding_mismatch[schedule]`
- [推測] `test_live_v4_does_not_call_attempt_registry_inspector`
- [推測] `test_live_v5_calls_inspector_and_compares_reported_to_independent_proof`
- [推測] 各v5 testはhonest v4 artifactをschema/key/proofだけv5へ変換し、perf、admission、session、binary各gateが同じ入力を拒否しないことを先にassertする。

### 必須負例と観測gate

| 負例 | 観測node / 他gateに遮られない理由 |
|---|---|
| [推測] v4に`attempt_registry` | pure verifier直接。honest v4へtop-level keyだけ追加 |
| [推測] proof field欠落 | core validator直接。top-level `attempt_registry` 自体は存在 |
| [推測] head改竄 | shape、binding、Nはvalid。pure equalityまたはB2 head比較だけが拒否 |
| [推測] N行内chain改竄 | canonical JSONとpath/bindingを維持。full replayのevent hash検査だけが拒否 |
| [推測] N以後parse破損 | 先頭Nとproofは一致。full-tail parseだけが拒否 |
| [推測] N以後chain切断 | tail JSONとrow shapeはvalid。chain continuityだけが拒否 |
| [推測] N>len | proof型とheadはvalid。prefix長検査だけが拒否 |
| [推測] 別freeze/protocol/schedule | proof shape/N/headはvalid。外部binding比較だけが拒否 |
| [推測] row_count 0 / 非整数 | core validator直接で、artifactやfilesystem gateを通さない |
| [推測] digest hex不正 | core validator直接で、binding/path gateより下層を名指し |
| [推測] zero head | hex64としてはvalidなので、nonzero専用gateだけが拒否 |

## 9. (P3) 到達可能性

- [実測] `reserve_attempt_slot()` のv2 branchはconsumption markerを必須化し、markerが無ければ拒否する。`s8b_attempt_registry.py:1657-1737`
- [実測] testにはB1の実capabilityを作る `_v2_registry_capability_case()` と、それを渡してreserveする `_reserve_v2()` が既にある。`test_s8b_attempt_registry.py:243-313`
- [実測] `_v2_registry_capability_case()` はadmission claimからbinding/slotを導出し、v2 genesisを作る。`test_s8b_attempt_registry.py:251-285`
- [実測] `_reserve_v2()` は `consumption_marker=case["capability"]` を渡し、production adapter経由でstart rowを作れる。`:288-313`
- [実測] 現状のv2 terminalはcoreとadapterの二層で拒否されたままだが、prefix正例に必要なgenesis 1行とreservation start行までは到達可能である。`:3000-3167`
- [実測] よって (P3) を採用する。B2-a正例はgenesis-onlyとgenesis+startの両方を実物経路で構成でき、不足入力はない。

# 依頼 3 — 変異事前登録候補

| ID | 変異位置 | 変異内容 | KILLED期待node | 他gateに遮られない理由 |
|---|---|---|---|---|
| [推測] M1 | `attempt_registry_core.py:266` 後の新validator | exact key検査を削除 | `test_attempt_registry_prefix_proof_rejects_missing_or_extra_key` | Mappingと残るfieldはvalid |
| [推測] M2 | 同validator | fieldごとのexact type検査をtruthy検査へ緩和 | `test_attempt_registry_prefix_proof_rejects_each_field_type[...]` | core直接呼出し |
| [推測] M3 | 同validator | `row_count > 0` を `>= 0` にする | `test_attempt_registry_prefix_proof_rejects_zero_row_count` | digestとkeyはvalid |
| [推測] M4 | 同validator | zero head拒否を削除 | `test_attempt_registry_prefix_proof_rejects_zero_head` | zeroはlowercase hex64なのでhex gateを通る |
| [推測] M5 | `s8b_attempt_registry.py:817` 後の新replay helper | live bytesを先頭N行へ切ってからreplayする | `test_prefix_inspection_rejects_malformed_tail_after_n` | 先頭Nとreported proofは一致。plan v2 M6の再照準 |
| [推測] M6 | 同replay helper | full replay後のrowsを使わずJSON decodeだけで済ませる | `test_prefix_inspection_rejects_broken_chain_after_n` | tailはcanonical JSONかつshape valid |
| [推測] M7 | 新`inspect_attempt_registry_prefix` | `len(rows) >= N` 検査を削除 | `test_prefix_inspection_rejects_n_beyond_live_rows` | proof shape/headはvalid |
| [推測] M8 | 同関数 | N行目head比較を削除 | `test_prefix_inspection_rejects_reported_head_tamper` | full replayとNはvalid |
| [推測] M9 | 同関数 | `rows[N-1]` を `rows[-1]` に変える | `test_prefix_inspection_accepts_valid_later_append` | append後の全行はcore-valid。D1337専用 |
| [推測] M10 | 同helper | v2 schema guardを削除して1段v1をproof対象にする | `test_prefix_inspector_rejects_canonical_one_level_v1` | v1自体はcore-valid |
| [推測] M11 | `s8b_floor_contract.py:81-87` の新v5 key集合 | v5から`attempt_registry`を落とす | `test_result_v4_key_contract_is_mode_conditional_and_exact` | mode/perf key集合は正しい |
| [推測] M12 | `s8b_floor_stats.py:734-768` の新proof比較 | reported/live exact equalityを削除 | `test_v5_rejects_reported_prefix_head_tamper` | proof shape、artifact、admissionはvalid。plan v2 M7の再照準 |
| [推測] M13 | `s8b_floor_stats.py:1036-1082` のv5分岐 | schema guardを削除しv4でもinspectorを呼ぶ | `test_live_v4_does_not_call_attempt_registry_inspector` | inspectorを呼ばれたら失敗するtripwireで直接観測 |
| [推測] M14 | 同wrapperのexpected binding構築 | external引数でなくreported proofのbindingを採る | `test_v5_rejects_proof_binding_mismatch[freeze/protocol/schedule]` | 各caseはN/head/replayがvalidでbindingだけ異なる |

- [実測] plan v2のM5はterminal coverageなので本scope外、M8はcandidate v5-onlyでD2、M9はearlier-result inspectionでD2である。今回は登録しない。
- [推測] plan v2のM6はM5/M6へ、M7はM12へ再照準して本scopeへ含めた。

## 総括

- [推測] 分割判定: B2-a + D1-a〜dは1 wave、実装子2本、fix 3巡以内で安全に扱える。
- [推測] 規模: production changed LOC 約314〜502、test 38新設 + 2更新、総code差分約750〜1,190行。
- [実測] (P1) 採用: producerと`RESULT_SCHEMA`はv4のまま、v5は`RESULT_SCHEMA_V5`。
- [実測] (P2) 一部採用: APIはadapter、admission直importは循環/meta-testのため却下。launcher/statsが呼ぶ。
- [実測] (P3) 採用: B1 capability経由でv2 genesis+reservation正例を構成できる。
- [実測] (P4) 採用: `schema` kw-only default=v4、D2 fileは変更しない。
- [推測] (P5) 採用: wave分割不要。安定checkpointは `D1-b+B2-a` → `D1-a+c+d`。
- [推測] (P6) 一部変更: file所有2本は採用するが、重複定義を避け内部順はD1-b→B2-aとする。
- [実測] pytestは未実走であり、緑は主張しない。