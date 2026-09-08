`git diff HEAD --stat` は指定された所有 4 ファイルだけで、所有外差分はありません。pytest は実行していません。

## A-1: terminal field の参照規則が consumer と不一致

- **主張:** producer は常に `payload` 内を読みますが、consumer の `_wal_field()` は同名の top-level field を優先します。このため `derive_physical_result()` が発行可能と判定した値を consumer が FC07 で拒否できます。
- **根拠:** producer は `payload.build_attempt_id`、`payload.verify_configs`、`payload.reason`、`payload.verify` を読む一方、consumer は `reflux_formal_consumer.py:1095-1099` で top-level を優先し、`1144-1263` で検査します。具体例:

  - `VerifyResult`: `serializable=False`, `n_txns=n_reads=n_writes=n_keys=n_edges=2`, `total_cycles=1`, clean integrity、anomaly は `cycle=[1,2]`, `phenomenon="G2"`、2 本の `rw` edge。
  - terminal: `stage="abort"`, top-level `reason="indeterminate"`、`payload.reason="non-serializable"`, `payload.build_attempt_id="A"`, `payload.verify=result_to_dict(vr)-trace_dir`。
  - 非書込 probe では producer は `outcome="rejected"`, `constraint_sha256="64ef61062db5c800cdd31bacb3ac0915e30342146995d885553cf0f53a89f101"` を返しました。consumer は top-level reason を読み FC07 です。

  accepted でも、top-level `verify_configs=[]`、`payload.verify_configs=["legacy","s2"]`、`payload.build_attempt_id="A"` なら producer は accepted、consumer は FC07 です。top-level を `["legacy"]` または `["s2","legacy"]` にすれば部分一致、順序違いも同様です。top-level `verify=S_B` と payload `verify=S_A` なら snapshot 不一致も迂回できます。top-level と payload の `build_attempt_id` が異なる場合は projection attempt 判定または `reflux_result_evidence.py:1121-1122` で FC07 より前に拒否されます。
- **帰結:** canonical-list projection に同名 top-level field があるだけで、producer が consumer 不受理の result record を導出できます。
- **推奨:** **must-fix**。producer と consumer で同じ field accessor を共有するか、同名 top-level field を producer と projection resolver の双方で明示拒否してください。
- **確度:** 高。現物コードと純粋関数 probe で確認済みです。

## A-2: 導出結果と issuer が参照する WAL が結合されていない

- **主張:** `derive_physical_result()` に渡した records と、`assemble_result_evidence_record()` に渡す `ordered_wal_ref` は独立です。さらに issuer は参照先 bytes の digest しか検査せず、projection、source interval、attempt、terminal outcome を検証しません。
- **根拠:** 導出は `reflux_result_evidence.py:488-588`、独立した ref の組立は `694-727`、issuer の generic resolve は `858-872` です。consumer の semantic resolve は `1063-1122`、FC07 検査は `reflux_formal_consumer.py:1133-1264` にあります。

  具体的には、同じ attempt `"A"` に対して anomaly `A=[1,2]` の `VerifyResult` から `H(A)` を導出し、record の `ordered_wal_ref` には anomaly `B=[3,4]` の valid terminal を持つ projection を指定できます。両 ref の digest とファイルが存在すれば issuer は record を書きますが、consumer は terminal から `H(B)` を計算し、`H(A) != H(B)` で FC07 にします。invalid projection bytes や不正 provenance でも、直接参照先の digestさえ一致すれば issuer は書込み可能です。
- **帰結:** A-1 の「typed result と terminal WAL の束縛」が public issuance 経路では成立せず、consumer-invalid artifact を実際に作成できます。
- **推奨:** **must-fix**。issuer が resolved projection records から再導出する一体 APIにするか、`DerivedPhysicalResult` に projection identity/digest を保持して assemble/issue 時に exact 一致を検査してください。
- **確度:** 高。

## A-3: M2〜M5 は重複検査に mask される

- **主張:** 事前登録された M2〜M5 は、指定位置を単独変異しても別層の同じ条件で拒否されます。「殺した」という author 報告は静的到達性と一致しません。
- **根拠:**

  - M2: typed clean 検査 `reflux_result_evidence.py:553` を落としても wire clean と counter 検査 `444-449` が拒否。
  - M3: `len(anomalies)==1` は `476` と `563` の二重検査。
  - M4: capped 値 `total_cycles=4, len(anomalies)=1` は `562` で拒否され、登録位置 `483` に到達しません。
  - M5: empty 値は `562`, `563`, `476` の複数理由で拒否。
  - `cycle[0]=True` は r9 の cycle が最小 txid `0` から始まるため、exact 型 `330` に加えて edge ring `346-347` にも違反します。
  - `unknown-phenomenon` は allowlist `324` と派生 phenomenon 一致 `399` の二理由です。

  また `482` の「cardinality は drift assertion」という comment は不正確です。`anomaly_count == len(anomalies)` は恒真ですが、`total_cycles == anomaly_count` は切詰めを拒否する実防護です。
- **帰結:** mutation matrix が実際より強く見え、dirty、複数、切詰め、空 anomaly の拒否条件を一つずつ失う変異を検証できていません。
- **推奨:** **must-fix**。重複判定を一つの policy function に集約するか、各変異を全重複位置に適用する複合変異として再登録してください。comment も恒真条件と切詰め防護を分けてください。
- **確度:** 高。

## A-4: 境界テストと issuance 統合が不足

- **主張:** `verify_configs` の負例は `["wrong"]` 一件だけで、部分一致、同一要素の順序違い、空を直接 pin していません。また端から端正例は実 issuer を通りません。
- **根拠:** `test_reflux_result_evidence.py:646-671` の accepted 負例は `["wrong"]` のみです。これは M1 の equality 全削除は殺しますが、prefix 比較や sorting/set 化は殺しません。統合テストは実 verifier を `test_reflux_formal_consumer.py:820-830` で呼んでいますが、record は `945` の fixture `write_evidence_tree()` で書き、`issue_result_evidence_record()` を迂回します。
- **帰結:** A-1 の field shadowing、A-2 の records/ref 取り違え、prefix・整列による将来の受理集合拡大が回帰テストに残りません。
- **推奨:** **must-fix**。空、正しい prefix、逆順、top-level shadow の各負例と、derive から実 issuer、consumer まで同じ resolved WAL を通す正例・取り違え負例を追加してください。
- **確度:** 高。

## A-5: shared wrapper 自体は受理集合不変

- **主張:** witness validator/digest の shared 化そのものには受理集合の変化を認めませんでした。
- **根拠:** validator 本体は関数名を除いて旧 consumer と AST 同値です。digest 式も同じで、`ArtifactError -> FC07` は `reflux_formal_consumer.py:1106-1110` に残っています。旧 `_ANOMALY_KEYS` から `_CLEAN_WIRE_COUNTER_KEYS` まで全 13 名が `114-137` で再 export されています。sorting、重複排除、prefix、float 許容の追加はありません。既存 test の削除・skip・期待値反転もなく、変更された既存 test は monkeypatch owner の移動 `test_reflux_formal_consumer.py:2065-2077` だけです。
- **帰結:** shared 化単体では既存 FC07 acceptance set を変えません。
- **推奨:** **nit**。この部分は維持してよいです。
- **確度:** 高。

## 変異×位置×nodeid

以下の「殺す」は pytest 実測ではなく、現物コードの静的到達性です。

| ID | 実位置と old 逐語 | 殺す予定の実在 nodeid | 静的判定 |
|---|---|---|---|
| M1 | `reflux_result_evidence.py:528` `tuple(verify_configs) != verifier_order` | `orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_terminal_mismatch[wrong-verify-configs]` | equality 全削除は殺す。prefix、sort、set 変異は未被覆 |
| M2 | `reflux_result_evidence.py:553` `and verify_result.integrity.clean() is True` | `...::test_synthetic_silo_source_refuses_dirty_nonserializable_result` | **mask**: `444-449` が拒否 |
| M3 | `reflux_result_evidence.py:563` `or len(verify_result.anomalies) != 1`、重複 `476` | `...::test_synthetic_silo_source_refuses_multiple_witness_classes` | **mask**: 一方を変えても他方が拒否 |
| M4 | `reflux_result_evidence.py:483` `total_cycles != anomaly_count` | `...::test_synthetic_silo_source_refuses_truncated_multiple_witness_classes` | **mask**: `562` で先に拒否 |
| M5 | `reflux_result_evidence.py:476,563` `len(anomalies) != 1` | `...::test_synthetic_silo_source_refuses_empty_capped_witness_report` | **mask**: `562` を含む複数拒否 |
| M6 | `reflux_result_evidence.py:485` `return validate_witness_anomaly(anomalies[0])` | `...::test_synthetic_silo_source_refuses_nonproduction_witness_shape[ring-mismatch]` | 殺す |
| M7 | `reflux_result_evidence.py:403` `return hashlib.sha256(canonical_json_bytes(anomaly)).hexdigest()` | `...::test_synthetic_silo_source_shared_witness_digest_matches_independent_bytes` | helper の変異は殺す |
| M8 | `reflux_result_evidence.py:576-579` `canonical_json_bytes(payload.get("verify")) == canonical_json_bytes(snapshot)` | `...::test_formal_consumer_contract_refuses_terminal_mismatch[different-run-snapshot]` | 殺す |
| M9 | `reflux_result_evidence.py:573` `payload.get("reason") != verify_result.verdict` | `...::test_formal_consumer_contract_refuses_terminal_mismatch[wrong-reason]` | 殺す |
| M10 | `reflux_result_evidence.py:586` `"rejected"` | `...::test_synthetic_silo_source_derives_rejected_single_witness_class[r9_dense_cycle4]` | 殺す |
| M11 | `reflux_result_evidence.py:542` `DerivedPhysicalResult(build_attempt_id, "accepted", None)` | `...::test_formal_consumer_contract_derives_accepted_commit_terminal` | 殺す |
| M12 | `reflux_result_evidence.py:727` `return validate_result_evidence(record)` | `...::test_formal_consumer_contract_assembler_rejects_invalid_input` | 殺す |
| M13 | `reflux_result_evidence.py:865-872` 2 回の `resolve_content_addressed_ref(...)` の後に `write_result_evidence_record(...)` | `...::test_formal_consumer_contract_issuer_resolves_before_record_creation` | 順序反転は殺す。ただし semantic resolve 欠落は未検出 |
| M14 | `reflux_result_evidence.py:419` `type(stats[key]) is int` | `...::test_synthetic_silo_source_refuses_nonexact_typed_values[stats-bool]` | この位置は殺す。cycle/version の別 exact 型位置までは代表しない |
| M-C1 | `reflux_formal_consumer.py:1107-1110` `except ArtifactError as exc: raise _ContractFailure(FormalReasonCode.FC07) from exc` | `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_converts_witness_canonicalization_artifact_error` | 殺す |

`anomaly_count == len(anomalies)` の単独削除は、public producer が `result_to_dict()` だけを通る限り等価変異です。一方 M2〜M5 は等価ではなく、他層 mask です。

## 総括

must-fix は 4 件です。  
最重は、terminal field の読み方の不一致と、導出 records と発行 ref の未結合により consumer-invalid record を発行できることです。  
shared validator/digest の逐語移動と `ArtifactError -> FC07` は支持します。  
M2〜M5 の mutation kill 主張は静的に成立しません。  
pytest は実行しておらず、must-fix 解消前の実装全体は支持しません。