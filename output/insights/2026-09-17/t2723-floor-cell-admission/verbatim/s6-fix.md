## 変更一覧

- `orchestrator/campaign/p3_b4_floor_artifact_issuer.py:34`：module import を bootstrap 後の相対 sibling import へ移動し、名前順を整理。
- `orchestrator/tests/test_p3_b4_admission_record.py:1173`：`test_section5_parser_preserves_raw_and_normalized_values` の入力 label を padded spelling に変更。normalized key・strip 前 label・raw/normalized 値を検証。
- `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:908`：`test_resolver_accepts_valid_pin_with_other_cells_unrecorded` を追加。`_SECTION5_LABELS` から指定 5 欄を取得して `未記入` に置換し、有効 pin の artifact path/hash が一致することを検証。

今回の差分は以上の 3 file のみ。禁止対象は未編集です。

## 実走結果

指定コマンドを実行し、いずれも rc=0。

| コマンド | passed | failed |
|---|---:|---:|
| `PYTHONPATH=. python3 orchestrator/tests/test_p3_b4_floor_artifact_issuer.py` | 94 | 0 |
| `PYTHONPATH=. python3 orchestrator/tests/test_p3_b4_admission_record.py` | 30 | 0 |

各 file 全件を実走。今回追加・補強した nodeid も成功しました。

- `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py::test_resolver_accepts_valid_pin_with_other_cells_unrecorded`
- `orchestrator/tests/test_p3_b4_admission_record.py::test_section5_parser_preserves_raw_and_normalized_values`

`git diff --check` も成功。material report・import invariant・変異 matrix は今回未実走です。提供された焦点ログでは import invariant は skip されており、赤の本文は確認できませんでした。

## 期待値変更

段 5 以前の既存 test の期待値は変更していません。

指定に従い、段 5 追加 test `test_section5_parser_preserves_raw_and_normalized_values` の `verbatim_labels[label]` 期待値だけを `label` → `f" {label} "` に変更しました。値側の `"A"` / `"Ａ"` は維持しています。

## 受理集合の自己申告

段 5 tip から受理集合の変化はありません。production の変更は import の相対化・移動のみで、判定処理は不変です。

静的な波及確認では、`_floor_cell` の caller は issuer 内 resolver、production の resolver consumer は `p3_b4_material_report.py:216`。admission 検査の内部 caller は `p3_b4_admission_record.py:822` です。共有 fixture は floor test の `_preregistration` → admission test の `_section5_document`、material report test の 137・1001・1110 行 → `_preregistration` という既存関係を維持しています。

継承した変異 matrix の対象と予想 killer は以下です。A＝`orchestrator/campaign/p3_b4_admission_record.py`、F＝`orchestrator/campaign/p3_b4_floor_artifact_issuer.py`。killer は未実測です。

| 変異 | 対象 file:line | 予想 killer（test 関数名） |
|---|---|---|
| M0 | A:27 | 等価変異、SURVIVED 予想 |
| M1 | F:1475 | `test_resolver_ignores_pin_outside_section5` |
| M2 | F:1495 | `test_resolver_rejects_unrecorded_owner_before_loading_pin` |
| M3 | A:658 | `test_resolver_rejects_unknown_label_at_fixed_row_count` |
| M4 | A:650 | `test_resolver_exact_sentinel_is_the_only_absence` |
| M5 | A:656 | `test_section5_parser_preserves_raw_and_normalized_values` |
| M6 | A:615 | `test_resolver_ignores_blocked_section5_decoys[fence]` |
| M7 | A:615 | `test_resolver_ignores_blocked_section5_decoys[comment]` |
| M8 | F:1525 | `test_resolver_preserves_raw_floor_pin` |
| M9 | F:1488 | `test_resolver_keeps_exact_floor_label[padded]` |
| M10 | F:1523 | `test_resolver_rejects_nfkc_only_absent_sentinel` |
| M11 | F:1495 | `test_resolver_accepts_valid_pin_with_other_cells_unrecorded` |

## 総括

指定の 3 件を修正済み。直接実行テストは合計 **124 passed / 0 failed**。受理集合の追加変更、test の弱体化、commit・git add はありません。
