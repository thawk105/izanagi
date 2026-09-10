## 判定式

`orchestrator/campaign/reflux_formal_consumer.py:822-880` を次の方針で変更する。既存 import の `hashlib`、`ArtifactError`、`canonical_json_bytes` だけを使い、新しい直列化形式や reason code は作らない。

`_wal_field()` の直後、`_verifier_policy()` の前へ置く補助関数:

```python
_CANDIDATE_ATTRIBUTABLE_ABORT_REASONS = frozenset({
    "non-serializable",
})

_WITNESS_UNORDERED_LIST_FIELDS = frozenset({
    "cycle",
    "edges",
    "types",
    "reasons",
})


def _normalize_witness_value(
    value: object,
    *,
    list_field: str | None = None,
) -> object:
    if type(value) is float:
        raise ArtifactError("witness class forbids floating-point values")
    if type(value) is dict:
        return {
            key: _normalize_witness_value(item, list_field=key)
            for key, item in value.items()
        }
    if type(value) is list:
        normalized = [
            _normalize_witness_value(item)
            for item in value
        ]
        if list_field in _WITNESS_UNORDERED_LIST_FIELDS:
            unique = {
                canonical_json_bytes(item): item
                for item in normalized
            }
            return [unique[raw] for raw in sorted(unique)]
        return normalized
    return value


def _normalized_witness_class_sha256s(
    anomalies: object,
) -> tuple[str, ...]:
    if type(anomalies) is not list or not anomalies:
        return ()
    if any(type(anomaly) is not dict for anomaly in anomalies):
        return ()
    try:
        return tuple(sorted({
            hashlib.sha256(
                canonical_json_bytes(_normalize_witness_value(anomaly))
            ).hexdigest()
            for anomaly in anomalies
        }))
    except ArtifactError:
        return ()
```

`_validate_wal_outcomes()` の rejected 枝 `orchestrator/campaign/reflux_formal_consumer.py:867-879` は次へ置換する。

```python
        else:
            _require(FormalReasonCode.FC07, terminal.get("stage") == STAGE_ABORT)

            verify = _wal_field(terminal, "verify")
            _require(FormalReasonCode.FC07, type(verify) is dict)

            reason = _wal_field(terminal, "reason")
            candidate_attributable = (
                type(reason) is str
                and reason in _CANDIDATE_ATTRIBUTABLE_ABORT_REASONS
                and type(verify.get("verdict")) is str
                and reason == verify["verdict"]
            )

            total_cycles = verify.get("total_cycles")
            anomaly_count = verify.get("anomaly_count")
            not_truncated = (
                type(total_cycles) is int
                and total_cycles >= 0
                and type(anomaly_count) is int
                and anomaly_count >= 0
                and total_cycles == anomaly_count
            )

            witness_class_sha256s = (
                _normalized_witness_class_sha256s(verify.get("anomalies"))
            )
            _require(
                FormalReasonCode.FC07,
                candidate_attributable
                and not_truncated
                and len(witness_class_sha256s) == 1
                and witness_class_sha256s[0]
                == physical["constraint_sha256"],
            )
```

ここで読む WAL path はすべて実在する。

- `wal.abort.payload.reason`: `pipeline.py:1251-1254` が常に作る。
- `wal.abort.payload.verify`: verifier reject だけが `pipeline.py:1601-1604` で作る。
- `wal.abort.payload.verify.verdict`: `report.py:96-100`。
- `wal.abort.payload.verify.anomaly_count`: `report.py:134`。
- `wal.abort.payload.verify.total_cycles`: `report.py:135`。
- `wal.abort.payload.verify.anomalies`: `report.py:136`。
- 比較相手 `physical_result.constraint_sha256`: schema は `reflux_result_evidence.py:109-111`、rejected 時の SHA-256 検証は同 `291-304`。

`build_attempt_id`、terminal `stage`、accepted 枝、`_wal_field()` は変更しない。

## 述語の導出根拠

### Candidate attributability

`pipeline.py:1594-1604` では verifier が非 certified のときだけ、`reason=vr.verdict` と `verify=result_to_dict(vr)-{"trace_dir"}` を同じ abort payload に入れる。`VerifyResult.verdict` の閉じた値は `verifier/model.py:502-515` にあり、abort 到達値は次の二つである。

- `non-serializable`: cycle が実在し、candidate に帰属できる。
- `indeterminate`: 空 trace または integrity 不成立で、candidate 固有の constraint witness とは断定できない。

したがって positive allowlist は `non-serializable` だけとする。単なる `reason == verify.verdict` だけでは、未知の同値文字列を持つ合成入力まで通すため不十分である。未知 reason は既定で false になる。

偽になる実入力は、実在する `build-error` abort (`pipeline.py:1355-1360`) または `indeterminate` verifier abort である。前者は `verify` 自体がなく、後者は allowlist に含まれない。

### Truncation

- `report.py:134` は `anomaly_count = len(res.anomalies)` を書く。
- `report.py:135` は切詰め前の `res.total_cycles` を書く。
- `verifier/model.py:497-500` は `total_cycles` が全 SCC 数、`anomalies` が `max_report` で切り詰められ得ることを明記する。
- `mocc_g2_discriminator.py:498-503` は `total_cycles != len(anomalies)` を `verifier-anomaly-list-truncated` と判定する。

よって production の `anomaly_count` が `len(anomalies)` の射影であることを使い、FC07 では exact int の `total_cycles == anomaly_count` を非切詰め条件にする。bool は `type(...) is int` で除外する。

偽になる実入力は `total_cycles=2, anomaly_count=1` である。これは `max_report=1` で二つの SCC が見つかった実 verifier 出力として到達可能である。

### Witness class

anomaly の production 形状は `report.py:17-41,134-136` にある。各 anomaly を一つの witness class として次の順に正規化する。

1. 浮動小数を一つでも含めば導出失敗 `()` とする。production anomaly は整数、文字列、list、dictだけなので正例を失わない。
2. `cycle`、`edges`、`types`、`reasons` は列挙順が class を変えない集合的部分として、各要素を既存 `canonical_json_bytes()` で key 化し、重複排除して byte 順に整列する。
3. `u_ver` / `v_ver` の二要素 list など、意味を持つ list 順序は保存する。
4. dict key 順は `canonical_json_bytes()` の `sort_keys=True` (`reflux_origin_artifacts.py:55-67`) に委ねる。
5. anomaly ごとの canonical bytes を SHA-256 にし、anomaly 列全体も集合化、重複排除、整列する。
6. digest 集合の cardinality が 1 で、その唯一値が `physical_result.constraint_sha256` と exact 一致することを要求する。

偽になる実入力は、異なる edge/reason を持つ二つの anomaly である。`total_cycles=2, anomaly_count=2` でも digest 集合が二要素となり拒否される。

### 恒真でないこと

| 連言 | それだけを偽にする具体入力 |
|---|---|
| `_wal_field(terminal, "build_attempt_id") == attempt` | terminal の attempt を別 ID にする。 |
| `terminal.get("stage") == STAGE_ABORT` | rejected record に commit terminal を対応させる。 |
| `type(verify) is dict` | 実在する `build-error` payloadのように `verify` を持たせない。 |
| reason の positive allowlist | `reason="indeterminate"`、`verify.verdict="indeterminate"`。 |
| `reason == verify["verdict"]` | `reason="build-error"`、`verify.verdict="non-serializable"`。 |
| counter の exact int | `total_cycles=True, anomaly_count=True`。 |
| `total_cycles == anomaly_count` | `total_cycles=2, anomaly_count=1`。 |
| witness cardinality 1 | 相異なる二つの anomaly、両 counter は 2。 |
| physical constraint との exact 比較 | anomaly は一つのまま、record/ledger の constraint を別の有効な 64 桁値にする。 |

偽にできない連言はない。旧 `candidate_attributable is True` と `truncated is False` のような producer 自己申告は全廃する。

## abort reason の網羅列挙

列挙方法は、3 module の AST について次を全走査する。

- `_abort()`、`_prebuild_abort()`、callback `abort()`、`_abort_balanced_workload()` の全 call。
- `wal.log()` / `emit()` のうち stage が `STAGE_ABORT` の call。
- reason が変数の場合は代入元、定数の場合は import 元まで追跡する。
- 最後に `rg -n "abort|reason"` との和集合で、AST が拾わない f-string family と reader-only の参照を確認する。

| reason | writer / 根拠 | FC07 candidate 起因か |
|---|---|---|
| `non-serializable` | `pipeline.py:1594-1604`、値域は `verifier/model.py:511-512` | はい。唯一の allowlist 要素。 |
| `indeterminate` | 同上、値域は `verifier/model.py:505-515` | いいえ。確証不能であり witness constraint を帰属しない。 |
| `identity-error` | `pipeline.py:1198-1201`; `loop.py:508-534` | いいえ。identity 解決失敗。 |
| `admission-error` | `pipeline.py:1198-1201,1206-1233` | いいえ。admission 前段。 |
| `build-source-state-error` | `pipeline.py:1347-1354` | いいえ。build 前 source state。 |
| `build-error` | `pipeline.py:1355-1360,1372-1392` | いいえ。verifier witness 不在。 |
| `bench-binary-mismatch` | `pipeline.py:1422-1431` | いいえ。trace/verifier 未起動。 |
| `trace-timeout` | `pipeline.py:1463-1470` | いいえ。verifier 未到達。 |
| `trace-no-commit-witness` | `pipeline.py:1471-1498,1541-1548` | いいえ。trace 帰属不能。 |
| `trace-witness-unsupported-workload` | `pipeline.py:1499-1511` | いいえ。trace witness 未対応。 |
| `trace-run-nonzero-exit` | `pipeline.py:1519-1524` | いいえ。異常終了。 |
| `trace-empty` | `pipeline.py:1525-1532` | いいえ。空 trace。 |
| `trace-no-abort-counts` | `pipeline.py:1533-1540` | いいえ。計器不足。 |
| `trace-batch-commits-unattributed` | `pipeline.py:1549-1555` | いいえ。commit 帰属不能。 |
| `trace-parse-error` | `pipeline.py:1556-1571` | いいえ。parser 失敗。 |
| `screen-slower-than-floor` | 定数 `pipeline.py:159-160`、writer 同 `1668-1680` | いいえ。candidate 固有でも性能 screening であり verifier witness ではない。 |
| `verify-probe-error` | `pipeline.py:1698-1707` | いいえ。環境 probe 失敗。 |
| `verify-competing-tenant` | `pipeline.py:1709-1714` | いいえ。測定環境競合。 |
| `bench-probe-error` | `pipeline.py:775-785`; balanced path `2117-2129` | いいえ。環境 probe 失敗。 |
| `bench-competing-tenant` | `pipeline.py:786-789`; balanced path `2131-2137` | いいえ。測定環境競合。 |
| `bench-unsettled` | `pipeline.py:801-807,2091-2106` | いいえ。測定環境未静定。 |
| `bench-returncodes-round-unbound` | `pipeline.py:809-818` | いいえ。測定 round 帰属不能。 |
| `bench-no-throughput` | `pipeline.py:820-826,2163-2196` | いいえ。性能観測不能。 |
| `bench-cv-undefined` | `pipeline.py:827-836,2244-2250` | いいえ。性能統計不能。 |
| `balanced-peer-prepare-failed` | `loop.py:665-671` から `_abort_balanced_workload()` | いいえ。peer arm の準備失敗。 |
| `eval-exception: <type>: <message>` | dynamic family、`loop.py:628-648` | いいえ。予期しない例外。 |
| `diff-quarantine` | `p3_s4_loop.py:703-739`、値は `critic/digest.py:200` | いいえ。candidate 検疫結果だが verifier anomaly class ではない。 |

補足として、`loop.py:448-466` が読む recovery abort には `recovery-abort-incomplete-attempt` と A1 用 `a1-balanced5-interrupted-attempt-invalid` もある。実 writer は要求された3 module外の `wal.py:2595-2626` であり、いずれも `verify` を持たないため FC07 では false になる。

この実装は denylist ではなく一要素の positive allowlist なので、将来 reason が追加されても自動受理されない。

## token 表と fixture の同期

- `reflux_source_closure.py:84-87` の  
  `wal.abort.payload.witnesses`  
  を  
  `wal.abort.payload.verify.anomalies`  
  へ変更する。
- consumer が digest 導出に読む実 path と一致し、`pipeline.py:1601-1604`、`report.py:136` に producer 根拠がある。
- exact 比較は `reflux_source_closure.py:224-237`、特に `:236`。fixture 側も同じ tuple でなければ positive issuance が拒否される。
- `reflux_origin_fixture_builder.py:305-313` の同じ literal を同時に `wal.abort.payload.verify.anomalies` へ変更する。
- `reflux_origin_fixture_builder.py:45-47` の任意 label hash は廃止し、整数・文字列だけから成る G2 anomaly fixture を定義した後、fixture 独自の `_sha256()` (`:76-81`) で `_CONSTRAINT_SHA256 = _sha256(_WITNESS_ANOMALY)` と導く。新しい hash literal は置かない。
- `_wal_records()` の abort payload `:376-386` は旧三 field を削除し、production 同様に `reason`, `build_attempt_id`, `build_admission_receipt_sha256`, `verify`, `workload` を持たせる。`verify` には少なくとも `report.py:96-137` と同じ full result shapeを入れ、`trace_dir` だけを除く。
- `verify` の positive 値は `verdict="non-serializable"`, `certified=False`, `serializable=False`, `anomaly_count=1`, `total_cycles=1`, `anomalies=[_WITNESS_ANOMALY]` とする。
- `physical_result.constraint_sha256` の二使用箇所 `reflux_origin_fixture_builder.py:463-467,649-653` は、導出済み `_CONSTRAINT_SHA256` を引き続き参照する。
- `test_reflux_formal_consumer.py:843-952` の旧 field mutation はすべて `payload.verify.*` の mutation へ移す。既存期待値は緩めず、旧三 fieldだけの terminal は FC07 のままにする。

## pin の同期

変更後の実物から実装子が再計算する。ここでは新しい hash 値を書かない。

`orchestrator/tests/reflux_origin_fixture_baseline.json` で canonical SHA-256 が変わる entry:

- `build_source_closure_record` (`:27-29`)
- `build_launch_admission_inputs` (`:11-13`)
- `build_recovery_envelope_inputs` (`:19-21`)
- `build_ordered_wal_projection` (`:15-17`)
- `build_result_evidence_record` (`:23-25`)

byte length も変更後の実物から再計算する。構造上変化するのは次の二つである。

- `build_source_closure_record`: runtime path の文字列長が変わる。
- `build_ordered_wal_projection`: full `verify` payload へ置換する。

他三 entry は 64 桁 digest の値だけが変わるため byte length は不変の見込みだが、実装子は推測値を採用せず全 entry を再計算する。`build_authority_manifest` と `build_execution_provenance` は依存入力が変わらないので hash、lengthとも不変である。

`orchestrator/tests/test_reflux_result_evidence.py:24-27` では次の4 literalを再計算する。

- `_RECORD_RAW_GOLDEN`
- `_LEDGER_EVIDENCE_DIGEST_GOLDEN`
- `_OUTER_SALTED_COMMITMENT_GOLDEN`
- `_WRONG_DOMAIN_PREFIXED_RAW_GOLDEN`

同 `:145-151` の raw record length `1848` は、record 内で変わる値が固定長 digestだけなので不変の見込みである。ただし実装時に実物で確認し、違えば実測値へ同期する。

第三の pin 不在は次の三経路で独立確認した。

1. 64桁 hex走査: `orchestrator/tests` の `\b[0-9a-f]{64}\b` は799箇所。現在の影響対象 hash に一致したのは baseline の5 entryと `test_reflux_result_evidence.py` の4 literalだけだった。
2. 生成関数 caller追跡: builder外の直接 callerは10 test file。さらに `test_reflux_originless_compatibility.py:13,126-140` が `test_p3_autonomous_workload_trial.py` の helper経由で間接利用する。caller先に追加の literal pinはなかった。
3. `orchestrator/tests` 外の走査: builder symbol群および現在の影響対象 hashはいずれも0件だった。

baseline の正否は `test_reflux_origin_fixture_builder.py:107-119` が全 builder を独立再計算して exact 比較する。

## 焦点走 file 集合

引き方は三段階とする。

1. 変更 production module名 `reflux_formal_consumer` と `reflux_source_closure` を `orchestrator/tests/*.py` から grepする。
2. 変更する `reflux_origin_fixture_builder.py` の全直接 callerを追う。
3. test helperを importする間接 callerも追う。これにより `test_reflux_originless_compatibility.py` を落とさない。

焦点走は次の12 file。

```text
orchestrator/tests/test_ccbench_spawn_sites.py
orchestrator/tests/test_p3_autonomous_workload_trial.py
orchestrator/tests/test_reflux_formal_consumer.py
orchestrator/tests/test_reflux_origin_artifacts.py
orchestrator/tests/test_reflux_origin_binding.py
orchestrator/tests/test_reflux_origin_client.py
orchestrator/tests/test_reflux_origin_fixture_builder.py
orchestrator/tests/test_reflux_origin_topology.py
orchestrator/tests/test_reflux_originless_compatibility.py
orchestrator/tests/test_reflux_result_evidence.py
orchestrator/tests/test_reflux_source_closure.py
orchestrator/tests/test_trial_registry.py
```

`test_ccbench_spawn_sites.py:174-175` は source-closure moduleを静的 inventory対象にする。`test_reflux_originless_compatibility.py:13,126-140` は P3 test helper経由の間接 consumerである。

## 変異事前登録候補

追加 nodeid 名は実装時にこの名前で固定する。

| 変異 id | 変異内容 | 期待 | 落ちると予測する nodeid |
|---|---|---|---|
| RW-01 | candidate allowlist の `non-serializable` を `indeterminate` にする | KILLED | `test_reflux_formal_consumer.py::test_fc07_accepts_production_verifier_reject_payload` |
| RW-02 | `reason == verify["verdict"]` を `True` にする | KILLED | `test_reflux_formal_consumer.py::test_fc07_rejects_non_verifier_reason_with_matching_witness` |
| RW-03 | `total_cycles == anomaly_count` を `True` にする | KILLED | `test_reflux_formal_consumer.py::test_fc07_rejects_truncated_verifier_anomaly_list` |
| RW-04 | counter の exact-int guardを削除する | KILLED | `test_reflux_formal_consumer.py::test_fc07_rejects_boolean_cycle_counts` |
| RW-05 | anomaly classの集合化をlist化し、重複を残す | KILLED | `test_reflux_formal_consumer.py::test_fc07_accepts_reordered_duplicate_witness_class` |
| RW-06 | float拒否を削除する | KILLED | `test_reflux_formal_consumer.py::test_fc07_rejects_float_witness_even_when_constraint_matches` |
| RW-07 | 複数 classから先頭一つだけを返す | KILLED | `test_reflux_formal_consumer.py::test_fc07_rejects_two_distinct_normalized_witness_classes` |
| RW-08 | physical constraintとの exact比較を `True` にする | KILLED | `test_reflux_formal_consumer.py::test_fc07_rejects_witness_digest_mismatch` |
| RW-09 | token pathを旧 `wal.abort.payload.witnesses` に戻す | KILLED | `test_reflux_source_closure.py::test_positive_fixture_validates_all_issuance_checks` |
| RW-10 | baseline の変更 entryを一文字壊す | KILLED | `test_reflux_origin_fixture_builder.py::test_baseline_schema_and_every_entry_match_independent_recalculation` |

SURVIVED を期待する変異は登録しない。全新規連言を少なくとも一つの独立負例で反転可能にする。

## 残る限界

- terminal record の outer key集合、型、重複、root shadow は閉じない。D1715の scope外判断を維持する。
- `_wal_field()` の rootからpayloadへの fallbackは残る。
- production pipelineは実在 verifier証拠をWALへ書くが、result-evidence record全体のproduction producerは依然存在しない。外部 producerが `constraint_sha256` を同じ規則で導出しなければFC07で止まる。
- normalizationは anomaly列、cycle、edge、type、reasonの列挙順と重複を消す一方、`u_ver` / `v_ver` の要素順など意味を持つ列は保存する。transaction IDの改名同値類までは作らない。
- 全検査通過後も `P6Unavailable` であり、`aborted=False` や certified選択集合は増えない。
- content-addressed evidenceは物理実行そのものを証明せず、evidence rootのtrusted first-writer仮定も残る (`reflux_result_evidence.py:1-10`)。

## 総括

FC07 rejected枝は旧三 fieldを一切読まず、実在する `reason` と `verify.*` だけから三述語を導く。  
候補帰属は `non-serializable` のpositive allowlistとverdict一致で閉じる。  
切詰めは全cycle数と報告anomaly数の一致、witnessは正規化digest集合のcardinality 1で閉じる。  
token path、fixture、baseline 5 entry、golden 4 literalを同じ変更単位で同期する。  
terminal外枠、result-evidence producer、P6は変更しない。