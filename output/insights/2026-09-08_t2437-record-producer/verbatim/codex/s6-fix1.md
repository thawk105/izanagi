## 所見×対応表 (closed/partial/regressed)

| 所見 | 状態 | 対応 |
|---|---|---|
| F-1 / A-2 / B-1 | closed | derive を canonical projection bytes 入力へ変更し、projection digest を assembler の ref digest と照合 |
| F-2 / B-2 | closed | synthetic source 限定、production 到達性非証明、salts 未行使、ledger replay 不要を docstring に明記 |
| F-3a / A-1 | closed | terminal record 外枠を production の 5 key exact に限定 |
| F-3b / A-4 | closed | verifier 順序の境界負例を追加し、33 record を実 issuer で発行 |
| F-3c / A-3 | closed | drift assertion と切詰め・単一 class 防護を 2 行の comment に分離。typed/wire 二重検査は維持 |
| A-5 | closed | 裁定どおり対応不要 |
| B-3 | partial | 受入所要台帳は親の所有。実測後の 36 nodeid 登録が残る |
| B-4〜B-7 | closed | fixture、golden、consumer contract、scope を維持 |
| regressed | なし | 指示外の受理集合変更なし |

## 編集面 (file:line)

- [reflux_result_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:137): production WAL 外枠 key 定義。
- [reflux_result_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:230): `DerivedPhysicalResult.ordered_wal_sha256`。
- [reflux_result_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:493): canonical projection の parse、attempt・records・terminal envelope 検査、digest 導出。
- [reflux_result_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:720): assembler の projection digest 照合。
- [test_reflux_result_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:135): projection bytes helper と derive 呼出し更新。
- [test_reflux_result_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:575): projection 不正、root shadow、verifier 順序、別 projection 負例。
- [test_reflux_formal_consumer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:813): docstring、projection bytes derive、33 件の実 issuer 発行。
- `reflux_formal_consumer.py` の stage 5 差分は変更していない。

## 実走結果

- 指定 2 test file を `tools/run_tests.py` 経由で実行: rc=16。`qstat -Q preflight rc=1` の dispatch infrastructure failure で child 未起動、実行 0 件。
- 両 test file の自走 harness: 各 rc=0。ただし `__main__` harness がなく、import のみ。pytest 緑とは扱わない。
- 新規境界面の直接 probe: 14 ケース、rc=0。
- fixture 構築、33 record の issuer 発行、formal consumer の `P6Unavailable` 到達 probe: rc=0。
- `py_compile` 対象 4 ファイル: rc=0。
- `git diff --check`: rc=0。

## 不変条件

- 指定不変面への `git diff --exit-code`: rc=0。

  - `reflux_origin_fixture_builder.py`
  - `reflux_origin_fixture_baseline.json`
  - `wal.py`
  - `pipeline.py`
  - `orchestrator/verifier/`

- `git status --short` は所有 4 ファイルのみ。
- 新規ファイル 0。docs、台帳、fixture、golden、WAL、pipeline は未編集。
- commit、push、branch 操作なし。

## nodeid 一覧 (新規・改名)

HEAD 比で合計 36 nodeid。今回の fix 追加はうち 12 件。

```text
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_derives_accepted_commit_terminal
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_invalid_ordered_wal_projection[noncanonical]
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_invalid_ordered_wal_projection[different-attempt]
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_invalid_ordered_wal_projection[empty-records]
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_terminal_root_shadow[reason]
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_terminal_root_shadow[verify-configs]
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_terminal_root_shadow[verify]
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_terminal_root_shadow[build-attempt-id]
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
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_nonexact_accepted_verifier_order[empty]
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_nonexact_accepted_verifier_order[prefix]
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_nonexact_accepted_verifier_order[reverse]
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_refuses_nonexact_accepted_verifier_order[duplicate]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonexact_typed_values[stats-bool]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonexact_typed_values[cycle-bool]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonexact_typed_values[reason-version-float]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonproduction_witness_shape[unknown-phenomenon]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonproduction_witness_shape[ring-mismatch]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_refuses_nonproduction_witness_shape[unknown-reason-type]
orchestrator/tests/test_reflux_result_evidence.py::test_synthetic_silo_source_shared_witness_digest_matches_independent_bytes
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_assembler_rejects_invalid_input
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_assembler_rejects_different_projection_same_attempt
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_issuer_resolves_before_record_creation
orchestrator/tests/test_reflux_result_evidence.py::test_formal_consumer_contract_issuer_writes_nine_keys_create_only
orchestrator/tests/test_reflux_formal_consumer.py::test_synthetic_silo_source_producer_passes_formal_consumer_contract
```

## 変異×nodeid 表

`R` は `orchestrator/tests/test_reflux_result_evidence.py`、`C` は `orchestrator/tests/test_reflux_formal_consumer.py`。

| 変異 | KILLED にする nodeid |
|---|---|
| M1 verifier exact 一致削除 | `R::test_formal_consumer_contract_refuses_nonexact_accepted_verifier_order[prefix]` |
| M2 clean 検査削除、typed/wire 複合 | `R::test_synthetic_silo_source_refuses_dirty_nonserializable_result` |
| M3 singleton 検査緩和、typed/wire 複合 | `R::test_synthetic_silo_source_refuses_multiple_witness_classes` |
| M4 total_cycles 検査削除、typed/wire 複合 | `R::test_synthetic_silo_source_refuses_truncated_multiple_witness_classes` |
| M5 empty 拒否削除、typed/wire 複合 | `R::test_synthetic_silo_source_refuses_empty_capped_witness_report` |
| M6 witness 構造検査削除 | `R::test_synthetic_silo_source_refuses_nonproduction_witness_shape[ring-mismatch]` |
| M7 canonical anomaly 以外から digest | `R::test_synthetic_silo_source_shared_witness_digest_matches_independent_bytes` |
| M8 terminal snapshot 照合削除 | `R::test_formal_consumer_contract_refuses_terminal_mismatch[different-run-snapshot]` |
| M9 reason と verdict の照合削除 | `R::test_formal_consumer_contract_refuses_terminal_mismatch[wrong-reason]` |
| M10 rejected を accepted に変更 | `R::test_synthetic_silo_source_derives_rejected_single_witness_class[r9_dense_cycle4]` |
| M11 accepted に constraint を付加 | `R::test_formal_consumer_contract_derives_accepted_commit_terminal` |
| M12 assembler validation 削除 | `R::test_formal_consumer_contract_assembler_rejects_invalid_input` |
| M13 resolve 前に record 作成 | `R::test_formal_consumer_contract_issuer_resolves_before_record_creation` |
| M14 exact int を `isinstance` に緩和 | `R::test_synthetic_silo_source_refuses_nonexact_typed_values[stats-bool]` |
| M-C1 `ArtifactError` から FC07 への変換削除 | `C::test_fc07_converts_witness_canonicalization_artifact_error` |
| M-F1 projection digest 照合削除 | `R::test_formal_consumer_contract_assembler_rejects_different_projection_same_attempt` |

M2〜M5 は裁定どおり、typed 層と wire 層を同時に変える複合変異として親側登録が必要。

## 未完・未実走

- 正式 pytest は dispatch infrastructure failure のため未実走。実装済みだが pytest 緑とは申告しない。
- 36 nodeid の collection/JUnit 実測と `acceptance_duration_ledger.json` への `--add-only` 登録は親作業。
- 実装上の未完、既知 regression はなし。

## 総括

F-1、F-2、F-3a〜c を実装した。  
projection bytes から derive した digest と record ref が一致しない限り発行できない。  
33 record の issuer 経由 integration probe は rc=0。  
正式 pytest と台帳登録のみ、基盤復旧後の親作業として残る。