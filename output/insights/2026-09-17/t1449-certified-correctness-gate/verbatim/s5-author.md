## 変更した file と差分の要約

変更は指定の2ファイルのみです。

- `orchestrator/submission_gate/_semantic_validator.py`: `_validate_reason_branches` の末尾に条件付き gate を追加。
- `orchestrator/tests/test_t338_submission_gate_unit3.py`: fixture に11ファイル、helper 3個、新規 test 11ケースを追加。

既存 test 全本文と `_full_receipt` 本文は変更前と一致。既存 fixture entry の順序・内容も維持しています。

## gate の実装 (行番号と code)

`_semantic_validator.py:2051` のコメントから追加。gate 本体は2054行目です。裁定 §2 と同じ変数名・条件・message です。

```python
    # Section 7.1(1) preserves 0-5 entries when verification records a failure;
    # require six pairs when performance completes with no verification outcome.
    # performance_slots passed the loop's raw checks, not just reason_code claims.
    verification_failure_recorded = any(
        isinstance(attempt, Mapping)
        and attempt.get("cluster_slot_or_null") is None
        and attempt.get("reason_code") != "completed"
        for attempt in attempts
    )
    if performance_slots and not verification_failure_recorded:
        evidence = value.get("correctness_evidence", ())
        evidence_pairs = {
            (entry.get("arm"), entry.get("workload"))
            for entry in evidence
            if isinstance(entry, Mapping)
        }
        expected_pairs = {(arm, workload) for arm in _ARMS for workload in _WORKLOADS}
        if len(evidence) != 6 or evidence_pairs != expected_pairs:
            _semantic(
                "correctness",
                "completed performance without a recorded verification failure "
                "requires six correctness arm/workload pairs",
            )
```

既存の検証 completed 分岐、他の分岐、docstring、呼出順、reason_code 語彙は不変です。

## fixture / helper

- `tree_files`: correctness JSON 5本と liveness log 6本を追加。
- `_certified_receipt`（658行）: deepcopy 後、検証 completed・correctness 6対・liveness 6対を構成。source は各 arm から複製し、entry 間で可変 dict を共有しません。
- `_without_verification_attempt`（699行）: deepcopy 後、検証 attempt だけを除去。
- `_completed_performance_reason_payload`（708行）: 単体試験用に36 planned/actual run が対応する最小 payload を構成。

`_full_receipt` の生成ロジック・返却構造は不変です。fixture へのファイル追加に伴う Git commit/tree identity は再計算されます。

## test (T1〜T8 の nodeid と、gate 削除で反転する根拠)

以下はすべて `orchestrator/tests/test_t338_submission_gate_unit3.py::` を接頭辞とする nodeid です。M1 は机上評価です。

| ID | nodeid | gate 削除時の挙動・根拠 |
|---|---|---|
| T1 | `test_certified_receipt_accepts_six_pairs` | 受理を維持。既存検証 completed 規則も満たす正例。 |
| T2 | `test_completed_performance_requires_correctness_top_level[0]`、`[1]` | 拒否→受理。検証 attempt がなく、先行検査は通り、不足件数を拒否する新 gate が消える。 |
| T3 | `test_completed_performance_requires_correctness_reason_branches[0]`、`[1]`、`[5]` | 拒否→受理。性能36-run 検査を満たし、検証 completed 分岐も通らないため。 |
| T4 | `test_completed_performance_rejects_duplicate_correctness_pair` | 拒否→受理。6件の ordinal・pointer 等は有効で、5対への被覆不足だけが残るため。 |
| T5 | `test_completed_performance_rejects_seven_correctness_entries` | 拒否→受理。単体入口なので schema 上限は介在せず、7件を拒否する gate が消える。 |
| T6 | `test_failed_performance_accepts_partial_correctness[0]`、`[5]` | 受理を維持。completed 性能 attempt がない正例。 |
| T8 | `test_recorded_verification_failure_accepts_empty_correctness` | 受理を維持。検証失敗記録による例外の正例。 |

T7 は提示された裁定表に定義がありません。正例 T1・T6・T8 は M1 で反転する試験ではありません。

## 実走結果 (nodeid と結果、未実走の列挙)

指定コマンドで次の全範囲を実走しました。

- `orchestrator/tests/test_t338_submission_gate_unit3.py`
- `orchestrator/tests/test_t338_submission_gate_unit5.py`
- `orchestrator/tests/test_t139_submission_path.py`

**133 passed、3 warnings、794.95秒、終了コード0。** 上表の新設11 node は全件成功しました。

unit5 の以下も成功しています。

- `test_conformance_vector_is_executed` の46 parameter 全件
- `test_conformance_index_has_complete_scoped_coverage`
- `test_receipt_publish_call_sites_are_path_aware_and_allow_event_sink`

追加の静的確認では、3 test file の関数名重複なし、既存 test 全本文の不変、validator の変更関数が指定関数のみであることを確認。`git diff --check` も成功しました。

指定範囲の未実走 node はありません。変異 M0〜M9 の実走は未実施です。3 warnings は外部 googletest の invalid escape sequence に関するものです。

## 変更前後の受理・拒否挙動

他の既存検査を満たす入力について：

| 入力 | 変更前 | 変更後 |
|---|---|---|
| 性能 completed＋検証 attempt なし＋evidence 0〜5件 | 受理 | `correctness` で拒否 |
| 性能 completed＋検証 pre_performance_infra_failure＋evidence 0〜5件 | 受理 | 受理を維持 |
| 性能 completed＋検証 completed＋完全6対 | 受理 | 受理を維持 |
| completed 性能 attempt なし＋部分 evidence | 受理 | 受理を維持 |

## 波及可能性の静的列挙

- `_writer.py:17,73`: validator を import し publish 前に呼ぶため、新 gate が間接適用されます。
- unit5: `_UNIT3._full_receipt` を正例・46 vector・writer 経路で使用。共有 helper 本文を維持し、全件回帰を実走しました。
- `test_t139_submission_path.py:24,42,48`: unit3 を読み込み、fixture を生成し、`tree_files` を複製するため、追加11ファイルも伝播します。同ファイル全件を実走しました。
- `_validate_study_receipts_inner`: 各受領証に単票 validator を呼ぶため、新 gate が間接適用されます。study 実装は変更していません。

新負例の直接検証は単体入口と top-level です。writer・study は呼出関係の確認と既存回帰による検証です。

## 未完・懸念

実装と指定回帰は完了しました。変異試験は親の段での実走が残っています。本環境の全走は約13分で、5分以内ではありませんでした。

commit・stage・branch 操作は行っていません。親の全走を本段の結果で代替しません。

## 総括

裁定どおりの条件付き最小 gate と正負例を、指定2ファイルに実装しました。既存検証失敗の受理を維持し、指定3ファイルの全133ケースが成功しました。