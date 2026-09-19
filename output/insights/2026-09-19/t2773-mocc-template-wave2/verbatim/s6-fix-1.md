## 変更 file 一覧

- [orchestrator/tests/test_mocc_template_proof.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2773-mocc-template-wave2/orchestrator/tests/test_mocc_template_proof.py)

F1 / F2 を実装。既存 13 node の名前・意味を維持し、所有外の変更はありません。

## per-key 対照の一覧

合成 proof / policy で全 30 check が True、`tuple(checks) == M.CHECK_KEYS` を確認。各対照では False になる key 集合全体を検査します。

| check key | 壊した入力 → 期待 False | 連鎖 |
|---|---|---|
| `template_stock_{w,u}_{hot,cold,default}_t{1,4}_certified_and_silent`（12 key） | txns・write ゼロ、certified False、cycle・X・P 非ゼロ、version_dups | summary または reason 総数不一致では matrix も False |
| `matrix_runs_complete_and_terminated` | 各走の終了状態、gate 2 本、admitted False、directive 変更 | なし |
| `template_off_stock_identity` | src_token を hex、digest 不一致、claim 変更 | ON も False |
| `template_on_benign_identity_distinct` | digest を OFF と同値、benign diff SHA 不一致 | なし |
| `trace0_logical_rows_identical` | off / on_b 各 flag・count・SHA 不一致、claim 変更 | なし |
| `trace0_nm_izanagi_zero` | count = 1 | なし |
| `trace0_strings_izanagi_trace_zero` | 各 count = 1 | なし |
| `toolchain_matches_policy` | g++ SHA 不一致 | なし |
| `template_touch_set_is_exact` | file 追加 | なし |
| `instrumentation_touch_set_is_transaction_only` | file 追加 | なし |
| `instrumentation_body_preserved` | 各 flag False、old / new SHA 不一致 | なし |
| `auditor_definition_read_only_and_projection` | 有効 projections を保持して Bash 追加、performance_rejected False、accepted_run False、wall_seconds 追加 | なし |
| `auditor_mocc_items_present` | 各 item False・欠落 | なし |
| `quarantine_accepts_benign_hole` | benign.passed False、case 追加・欠落 | case 集合変更では拒否側も False |
| `quarantine_rejects_frozen_frame_and_outside_edits` | stock-frame.subtype のみ変更 | なし |
| `auditor_digest_and_deny_only_controls` | machine-reject-preserved False・欠落 | なし |
| `consumer_binding_controls` | 各 key False | なし |
| `wave1_proof_bound_and_all_pass` | all_pass False、必要 check 欠落・False、path・SHA 形式不正 | なし |
| `legacy_proof_bound_and_all_pass` | 同上 | なし |

旧 proof の SHA を別の有効な hex に変えても `compute_checks` は通過します。実ファイルへの束縛は JSON consumer 側であることをコメントに明記しました。

## F2 の対照

X 条件全体を `false && (...)` で包み、3 flag の期待組を固定しました。

| 対照 | added_body | operation_contexts | line_restorations |
|---|---|---|---|
| X 恒偽化 | False | True | True |
| P 無効化 | False | True | True |
| publish 後へ移動 | False | False | True |
| `#line` +1 / -1 | True | True | False |

移動対照では diff 再生成により 2 本の `#endif` も追加行となるため、本文比較にも連鎖する旨を記載しました。

## 実走した検査

`PYTHONPATH=. python3 orchestrator/tests/test_mocc_template_proof.py`：**13 passed, 0 failed**。

以下の nodeid はすべて `orchestrator/tests/test_mocc_template_proof.py::` 接頭辞です。

```text
PASS test_mocc_auditor_definition_items_are_item_scoped
PASS test_mocc_auditor_projection_rejects_performance_fields
PASS test_mocc_mutation_surface_requires_auditor_live
PASS test_mocc_temperature_axis_contract
PASS test_mocc_template_checks_are_input_derived
PASS test_mocc_template_condition_gate_uses_new_driver_id
PASS test_mocc_template_consumer_binding_controls
PASS test_mocc_template_gate_activation_controls
PASS test_mocc_template_instrumentation_logical_rows
PASS test_mocc_template_instrumentation_preserves_body
PASS test_mocc_template_off_matches_stock_and_on_is_distinct
PASS test_mocc_template_proof_json_is_complete_and_bound
PASS test_mocc_template_quarantine_controls
```

system tmp の scratch 検査：

- 無変異対照：SURVIVED。
- M8：KILLED。subtype 単独変更対照で検出。
- M15：KILLED。allowlist の単純追加は正常 projection の完全一致検査で検出。
- M15 の追加確認として wall_seconds を任意許可する変異も KILLED。追加した wall_seconds 拒否対照で検出。

`git diff --check` 通過。AST 比較で 13 node の名前不変を確認しました。

## 総括

F1 / F2 完了。production code・受理集合は不変、commit は未作成です。依頼された検査の未実走項目はありません。

`git status --short`：

```text
 M orchestrator/tests/test_mocc_template_proof.py
```