## 読んだ資料

指定された7資料を読みました。

- `stage4-adjudication.md`（正本）
- `stage2-plan.md`
- `stage3-lensA.md`・`stage3-lensB.md`
- `brief.md`（段4の訂正を優先）
- `D922-verbatim.md`・`D1231-verbatim.md`

## 変更前の受理・拒否挙動

通常ファイルは main の同一 commit における `(path, mode, type, oid)` 一致で `landed`。限定された pure-add の負証拠では `not-landed` を返します。

spool は正式 receipt 一致だけで `landed`、不一致は `indeterminate`。削除 fragment は old blob の receipt を照合していました。

## S1 の実装 (file:line)

[check_branch_landed.py:731](tools/check_branch_landed.py:731)

- 最大1,024候補を tagged batch で照合。
- chunk 全行の終端・件数・連番・missing 式を検証。
- OID/type 一致候補を同じ commit の `_tree_entry` と `_entry_matches` で再確認。
- 空白類を含む path、削除、非通常状態は既存経路を維持。
- `:` を分解せず、上限超過時の正例優先も維持。

## S2 の実装 (file:line)

[check_branch_landed.py:1331](tools/check_branch_landed.py:1331)、[同:1418](tools/check_branch_landed.py:1418)

正常に解析できた通常 blob の receipt 不一致に、exact-state の正例専用 fallback を追加しました。

専用関数は `search`・`receipt_reason` だけを受け取り、`not-landed` を返しません。解析エラーを覆わず、削除 fragment は対象外です。exact 解決済み fragment は probe 対象から外れます。

## S4 の実装 (file:line)

[check_branch_rescue.py:1502](tools/check_branch_rescue.py:1502)、[同:1628](tools/check_branch_rescue.py:1628)

`unproven_unit_details` を追加しました。unit の commit・path・change・required state・理由・決定的証拠層と、理由別件数を運びます。

詳細は100件まで。超過時は `truncated`、子 report 不在・説明不足時は `complete: false` と欠落理由を返します。既存の判定・rc 計算は変更していません。

## 追加・改訂したテスト (nodeid)

以下の `L::` は `orchestrator/tests/test_check_branch_landed.py::`、`R::` は `orchestrator/tests/test_check_branch_rescue.py::` です。18関数を追加し、既存関数は変更していません。

**S1**

- `L::test_batch_path_handling`
- `L::test_batch_invalid_stdout_is_indeterminate`
- `L::test_batch_rejects_candidate_state_difference`
- `L::test_batch_preserves_merge_introduced_state`
- `L::test_batch_validates_all_rows_before_accepting_match`
- `L::test_batch_failure_never_becomes_negative`
- `L::test_batch_chunk_limit_and_command_count`
- `L::test_batch_empty_input_is_an_error`
- `L::test_batch_preserves_nonregular_legacy_path`

**S2**

- `L::test_spool_exact_history_without_receipt_is_landed`
- `L::test_unlanded_pure_add_spool_stays_indeterminate`
- `L::test_spool_exact_does_not_hide_integrity_errors`
- `L::test_unreceipted_spool_deletion_has_no_exact_fallback`

**S4・統合**

- `R::test_real_checker_unlanded_spool_details`
- `R::test_unproven_details_are_bounded_and_count_all_reasons`
- `R::test_missing_child_unit_details_never_claim_complete`
- `R::test_unit_details_do_not_change_assessment_decisions`
- `R::test_unit_details_do_not_change_rescue_rc_or_decision_inputs`

## 実走結果 (実走した nodeid と範囲、実走できなければその旨)

**実装済み・未実走です。実走した nodeid はありません。**

`tools/run_tests.py` から対象2ファイル全体と、次の制約検査を試行しました。

- `test_plain_runner_coverage.py` 全体
- `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`
- `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`

両試行とも `qstat -Q preflight rc=1` により harness が rc=16。`child_started=false` で pytest は起動していません。

静的確認では、4ファイルの構文解析・`git diff --check` が成功。AST 比較で既存テスト・共有 helper・既存定数が不変であることを確認しました。

## 所有外への波及可能性 (静的列挙)

- `acceptance_duration_ledger.json`：追加 nodeid の所要・被覆率確認が必要。
- `orchestrator/tests/conftest.py`：追加テストの収集・スケジューリング。
- `test_branch_rescue_ledger.py`・`test_check_docs.py`：rescue の契約・文書配線を検査する consumer。
- cleanup の棚卸し・報告 consumer：追加 JSON field と spool の証明改善を受け取ります。
- `report_sha256`：追加説明を含む report の内容に応じて変わります。

harness は dispatch receipt を自動生成しました。追跡対象の変更差分は指定4ファイルだけです。

## 実装しなかったもの と その理由

- **S3**：親の段6実測待ち。既存定数は不変。
- **X1〜X5**：段4で scope 外。
- 性能測定・変異 matrix・受入全走：未実施。
- docs 編集・commit・stage・push：指示どおり未実施。

## 総括

S1・S2・S4 と対応テストを実装しました。既存期待値は緩めていません。

**pytest 未起動のため、検証完了・closed とは申告しません。** 親による実走・性能測定・変異検査が残っています。