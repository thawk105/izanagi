## 編集面 (file:line)

- [reflux_result_evidence.py:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:222)
  - `ResultEvidenceIssuanceRefused`、`DerivedPhysicalResult`
  - shared witness validator/digest
  - terminal WAL と `VerifyResult` を束縛する三方向導出
  - 9-key assembler、参照先先行解決 issuer
  - S3 は未実装
- [reflux_formal_consumer.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:117)
  - shared 定数の module 属性再 export
  - [wrapper:1102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1102) のみ差し替え
  - `ArtifactError → FC07` 変換を維持
- [test_reflux_result_evidence.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:542)
  - synthetic Silo source、正例、全指定負例、assembler/issuer 検査
- [test_reflux_formal_consumer.py:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:813)
  - r9 1 回実走を33 recordへ使う新規 tmp evidence tree 統合テスト
  - salts 不変・未行使、ledger replay 非要求
  - [FC07 monkeypatch:2065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:2065) を shared owner へ変更

## 実走結果 (nodeid 範囲・件数・rc)

- 必須5ファイル束: `tools/run_tests.py` 経由で2回試行。`qstat -Q` preflight 失敗、child未起動、0件、`rc=16`。
- `orchestrator/tests/test_verifier.py::*`: 自走 harnessで105件成功、`rc=0`。
- `orchestrator/tests/test_plain_runner_coverage.py::*`: 自走 harnessで3件成功、`rc=0`。
- `py_compile`、`pyflakes`、`git diff --check`: 対象4ファイル、すべて`rc=0`。
- shared validatorの旧consumer本体とのAST同値、全shared定数のalias同値、consumer変更関数がwrapper 2件だけであることを静的検査済み。

## 不変条件の検査結果

`git diff --stat`:

```text
orchestrator/campaign/reflux_formal_consumer.py   | 171 ++-------
orchestrator/campaign/reflux_result_evidence.py   | 419 +++++++++++++++++++++-
orchestrator/tests/test_reflux_formal_consumer.py | 199 +++++++++-
orchestrator/tests/test_reflux_result_evidence.py | 397 +++++++++++++++++++-
4 files changed, 1028 insertions(+), 158 deletions(-)
```

次の不変面に対する `git diff --exit-code` は`rc=0`です。

```text
orchestrator/tests/reflux_origin_fixture_builder.py
orchestrator/tests/reflux_origin_fixture_baseline.json
orchestrator/campaign/wal.py
orchestrator/campaign/pipeline.py
orchestrator/verifier
```

変更ファイルは所有4ファイルだけです。docs、新規file、台帳、fixture、goldenに変更はありません。

## 新規 nodeid 一覧

以下はASTと明示param IDから確定した24件です。pytest collection自体はdispatch障害により未実行です。

```text
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_derives_accepted_commit_terminal
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_derives_rejected_single_witness_class[r9_dense_cycle4]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_derives_rejected_single_witness_class[r3_cycle3]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_derives_rejected_single_witness_class[r1_write_skew]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_indeterminate_result[integrity_orphan]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_indeterminate_result[m2_version_dup]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_dirty_nonserializable_result
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_empty_capped_witness_report
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_multiple_witness_classes
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_truncated_multiple_witness_classes
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_terminal_mismatch[different-run-snapshot]
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_terminal_mismatch[wrong-reason]
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_terminal_mismatch[wrong-verify-configs]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonexact_typed_values[stats-bool]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonexact_typed_values[cycle-bool]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonexact_typed_values[reason-version-float]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonproduction_witness_shape[unknown-phenomenon]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonproduction_witness_shape[ring-mismatch]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonproduction_witness_shape[unknown-reason-type]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_shared_witness_digest_matches_independent_bytes
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_assembler_rejects_invalid_input
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_issuer_resolves_before_record_creation
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_issuer_writes_nine_keys_create_only
orchestrator/tests/test_reflux_formal_consumer.py::test_synthetic_silo_source_producer_passes_formal_consumer_contract
```

## 変異×nodeid 表

| 変異 | 殺すnodeid |
|---|---|
| M1 | `test_formal_consumer_contract_refuses_terminal_mismatch[wrong-verify-configs]` |
| M2 | `test_synthetic_silo_source_refuses_dirty_nonserializable_result` |
| M3 | `test_synthetic_silo_source_refuses_multiple_witness_classes` |
| M4 | `test_synthetic_silo_source_refuses_truncated_multiple_witness_classes` |
| M5 | `test_synthetic_silo_source_refuses_empty_capped_witness_report` |
| M6 | `test_synthetic_silo_source_refuses_nonproduction_witness_shape[ring-mismatch]` |
| M7 | `test_synthetic_silo_source_shared_witness_digest_matches_independent_bytes` |
| M8 | `test_formal_consumer_contract_refuses_terminal_mismatch[different-run-snapshot]` |
| M9 | `test_formal_consumer_contract_refuses_terminal_mismatch[wrong-reason]` |
| M10 | `test_synthetic_silo_source_derives_rejected_single_witness_class[r9_dense_cycle4]` |
| M11 | `test_formal_consumer_contract_derives_accepted_commit_terminal` |
| M12 | `test_formal_consumer_contract_assembler_rejects_invalid_input` |
| M13 | `test_formal_consumer_contract_issuer_resolves_before_record_creation` |
| M14 | `test_synthetic_silo_source_refuses_nonexact_typed_values[stats-bool]` |
| M-C1 | `test_fc07_converts_witness_canonicalization_artifact_error` |

全変異に実在するtest定義があります。`anomaly_count == len(anomalies)`単独削除は裁定どおり等価変異です。

## 波及の静的列挙

指定grepの全hitです。

```text
orchestrator/campaign/reflux_formal_consumer.py:117:_ANOMALY_KEYS = result_evidence._ANOMALY_KEYS
orchestrator/campaign/reflux_formal_consumer.py:1102:def _valid_witness_anomaly(anomaly: object) -> bool:
orchestrator/campaign/reflux_formal_consumer.py:1106:def _witness_class_sha256(anomaly: object) -> str:
orchestrator/campaign/reflux_formal_consumer.py:1259:            _require(FormalReasonCode.FC07, _valid_witness_anomaly(anomalies[0]))
orchestrator/campaign/reflux_formal_consumer.py:1262:                _witness_class_sha256(anomalies[0])
orchestrator/campaign/reflux_result_evidence.py:147:_ANOMALY_KEYS = frozenset({"phenomenon", "length", "cycle", "edges"})
orchestrator/campaign/reflux_result_evidence.py:321:    if type(anomaly) is not dict or set(anomaly) != _ANOMALY_KEYS:
orchestrator/tests/test_reflux_formal_consumer.py:1606:    assert C._valid_witness_anomaly(report["anomalies"][0])
orchestrator/tests/test_reflux_formal_consumer.py:2072:        if type(value) is dict and set(value) == C._ANOMALY_KEYS:
```

所有外production callerはconsumerだけです。共有fixture builderにはhitなし、consumer testへの波及はvalidator正例とFC07例外変換の2面です。

## 未完・未実走

- 新規24件、`test_reflux_origin_fixture_builder.py`、既存consumer suiteはpytest未実走です。
- 既存FC07 testは41定義ありますが、今回の環境では緑を実測できていません。受理・拒否不変はwrapper限定差分とAST同値までの静的確認です。
- 原因はPegasus予約台帳更新不能からのdispatch、および`qstat -Q`失敗です。pytest専用allowlist対象を素のPythonで偽緑報告していません。
- commit、push、branch操作は実施していません。

## 総括

producer core APIと指定テストは所有4ファイル内へ実装済みです。  
verifier 105件とplain-runner 3件は自走緑、静的検査も緑です。  
必須pytest束はdispatch infrastructure障害で未実走のため、完了扱いにはできません。  
親側では新規24 nodeidの実collectionと既存FC07 41定義を含む再実走が必要です。