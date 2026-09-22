## 直した内容

- **G1:** `orchestrator/campaign/silo_policy_coverage.py:328` で、各 gate に他の診断 macro の CXX companion を渡さない形へ変更しました。実 patch の入れ子では追加 companion は不要で、軸の前提は configure 引数で維持し、gate 成功確認が build sink を支配する F1 の構造も保っています。
- **G2:** `orchestrator/campaign/condition_meaning_gate.py:85`・`:89` の指定 2 entry から companion を削除し、`orchestrator/tests/test_condition_meaning_gate.py:3426` の対応期待だけを追随しました。軸 define の重複供給を避け、probe / break の gate と build には `-DCCBENCH_SILO_POLICY_VARIANT=1` が渡ります。
- **G3:** `orchestrator/tests/test_ccbench_spawn_sites.py:2935` の本 wave の sink pin を **348 → 373** に更新しました。最終実装の build 呼び出しと一致させただけで、他の pin・検査条件は変更していません。
- **G4:** `orchestrator/campaign/silo_policy_coverage.py:416` に引数取得を共通化し、`:391`・`:588` から使用しました。`arguments` のキー存在で分岐するため、f3 の fixture `{"arguments": []}` も `command` 形式も扱い、TRACE=0 の清浄性判定は維持します。
- **G5:** `orchestrator/campaign/silo_policy_coverage.py:304` の拒否例外に、既存 driver と同じ `supply=状態/理由, meaning=状態/理由` を追加しました。拒否は引き続き build を止め、既存の `:679` の例外保存経路で結果 JSON の `error` にも理由が残ります。

G1 の最終構成です。A=`SILO_POLICY_VARIANT`、P=`IZANAGI_SILO_POLICY_PROBE`、B=`IZANAGI_BREAK_SILO_POLICY`。複数記載はそれぞれ別の gate 呼び出しです。

| case（方策） | gate する macro | CXX companion |
|---|---|---|
| norw（abort0 / maxwait） | A、`IZANAGI_BREAK_NOREAD_VALIDATION` | なし |
| lockskip（abort0 / maxwait） | A、`IZANAGI_BREAK_LOCK_COVERAGE` | なし |
| early-unlock（abort0 / maxwait） | A、`IZANAGI_BREAK_EARLY_UNLOCK` | なし |
| focus/focus | A、P | なし |
| focus/retry | A、P | なし |
| focus/huge | A、P | なし |
| mutation/no-clamp（huge） | B | なし |
| mutation/no-reload（retry） | B | なし |
| mutation/no-limit（retry） | B | なし |
| mutation/no-prefix-unlock-conflict（abort0、action-abort 出口） | B | なし |
| mutation/no-prefix-unlock-limit（maxwait、attempt-limit 出口） | B | なし |
| mutation/no-abort-hook（focus） | B | なし |
| mutation/no-lock-hook（focus） | B | なし |
| mutation/no-commit-hook（focus） | B | なし |
| mutation/wrong-reason（focus） | B | なし |
| TRACE=0（abort0） | A | なし |

機構変異は 8 種、prefix の 2 出口を分けて 9 case です。独立 build する正常対照は A、再利用する正常対照は対応する focus の A・P の証拠を使用します。

## 確認の実測

- 変更した **5 ファイルすべて `python3 -m py_compile` 終了コード 0**。生成キャッシュは `/tmp` 配下です。
- 読み取り AST 確認で `_build_variant` の `locks._run_cmake_build` は **373 行**、対応 pin も **373**。同ファイルを参照する他の登録に行番号 pin はありません。
- 追加テストは `test_silo_policy_coverage.py:377`・`:396`・`:436`・`:447`。

以下はすべて **実装済み・未実走** です。

| ファイル | node 名 |
|---|---|
| `orchestrator/tests/test_silo_policy_coverage.py` | `test_condition_gates_isolate_each_macro_and_keep_axis_cache` |
| 同上 | `test_build_requires_gate_before_configure_and_keeps_build_macros` |
| 同上 | `test_command_arguments_accepts_both_compile_command_forms` |
| 同上 | `test_condition_gate_rejection_preserves_arm_reasons_in_result_json` |
| 同上 | `test_coverage_reuses_controls_and_separates_prefix_exits` |
| `orchestrator/tests/test_condition_meaning_gate.py` | `test_v1_domain_and_claim_boundaries_are_exact` |
| 同上 | `test_compile_time_branch_selection_accepts_each_registry_macro[IZANAGI_SILO_POLICY_PROBE]` |
| 同上 | `test_compile_time_branch_selection_accepts_each_registry_macro[IZANAGI_BREAK_SILO_POLICY]` |
| 同上 | `test_new_branch_selection_supply_meaning_and_admission[IZANAGI_SILO_POLICY_PROBE]` |
| 同上 | `test_new_branch_selection_supply_meaning_and_admission[IZANAGI_BREAK_SILO_POLICY]` |
| 同上 | `test_new_branch_green_schema_rejects_count_value_and_argv_mutations[IZANAGI_SILO_POLICY_PROBE]` |
| 同上 | `test_new_branch_green_schema_rejects_count_value_and_argv_mutations[IZANAGI_BREAK_SILO_POLICY]` |
| `orchestrator/tests/test_ccbench_spawn_sites.py` | `test_production_build_sinks_include_certify_calibration_script` |
| 同上 | `test_define_sink_cross_product_has_no_unreviewed_ungated_member` |
| 同上 | `test_silo_policy_diagnostic_helper_sites_are_exact` |
| `orchestrator.campaign.silo_policy_coverage` | `coverage` / `smoke` |

## 変えていないことの根拠

- 許可 5 ファイルを除く通常ファイル **34,470 件**の変更前後の集約 SHA-256 は一致しました（`.git`、`__pycache__`、symlink は対象外）。
- 全文比較で、condition gate は指定 2 entry の companion 削除だけ、対応 test は新 macro の companion 期待変更だけ、spawn test は指定 pin の変更だけと確認しました。route・件数は変わらないため、その期待も維持しています。
- 既存 coverage テスト本文はバイト単位で不変です。追加したのは import と新規 4 テストだけです。
- docs・output は編集せず、git コマンド、test module の import・実行、build・driver 実走は行っていません。

## 未了と疑問

親による焦点走・coverage 再走が必要です。今回の確認は構文と読み取り比較までで、赤 8 件の解消や実機 gate 通過は未確認です。

## 総括

G1〜G5 を許可範囲内で修正し、構文確認と最終行番号の照合を完了しました。commit は作成していません。