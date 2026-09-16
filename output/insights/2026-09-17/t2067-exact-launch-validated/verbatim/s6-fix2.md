## 変更の要約

呼出位置を現物で1775行と確認し、pin を更新しました。allowlist は指定のアルファベット順位置へ1行追加しました。

`git diff --stat`:

```text
 orchestrator/tests/README.md                   | 1 +
 orchestrator/tests/test_ccbench_spawn_sites.py | 2 +-
 2 files changed, 2 insertions(+), 1 deletion(-)
```

`git diff`:

```diff
diff --git a/orchestrator/tests/README.md b/orchestrator/tests/README.md
index 1c1243ff8..49b0eccd4 100644
--- a/orchestrator/tests/README.md
+++ b/orchestrator/tests/README.md
@@ -163,6 +163,7 @@ pytest 専用テストで、`python3 file.py` 直接実行は no-op (偽緑で
 - test_s8b_budget_approval_preflight.py
 - test_s8b_descriptor.py
 - test_s8b_floor_stats.py
+- test_s8b_gate_core_exact_launch_validated.py
 - test_s8b_holdout_freeze.py
 - test_s8b_materialization.py
 - test_s8b_oracle_driver.py
diff --git a/orchestrator/tests/test_ccbench_spawn_sites.py b/orchestrator/tests/test_ccbench_spawn_sites.py
index 3e41959fa..38e368a1c 100644
--- a/orchestrator/tests/test_ccbench_spawn_sites.py
+++ b/orchestrator/tests/test_ccbench_spawn_sites.py
@@ -2978,7 +2978,7 @@ def test_define_sink_cross_product_classifies_t2155_production_sinks_exactly():
     s8b_sink = _BuildSink(
         "orchestrator/campaign/s8b_oracle_driver.py",
         "<module>.run_block",
-        1783,
+        1775,
         "campaign",
     )
     assert classifications[s1_sink] == Counter({
```

## 所見の対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| 赤1: spawn_sites の行番号 pin | closed | 1783 → 1775。対象 node を含む35件成功 |
| 赤2: plain_runner_coverage の allowlist | closed | 指定エントリ追加。全3件成功 |

## 実走結果

指定された `PYTHONPATH=. python3 -c "…pytest.main(…)…"` の起動形で実行しました。spawn_sites は node 表示用に `-v` を追加しました。

| 対象 | 結果 |
|---|---|
| `orchestrator/tests/test_plain_runner_coverage.py` | **3 passed**（5.42秒） |
| `orchestrator/tests/test_ccbench_spawn_sites.py -k "define_sink_cross_product or t2155"` | **35 passed, 12 deselected**（204.77秒） |
| `git diff --check` | 成功 |

spawn_sites の実走 nodeid は、共通接頭辞 `orchestrator/tests/test_ccbench_spawn_sites.py::` と以下の各名前を連結したものです。**全件 PASSED**。

```text
test_define_sink_cross_product_has_no_unreviewed_ungated_member
test_define_sink_cross_product_rejects_synthetic_member_without_gate
test_define_sink_cross_product_rejects_gate_with_only_one_arm
test_define_sink_cross_product_does_not_defer_unlisted_member
test_define_sink_cross_product_requires_gate_to_dominate_each_sink
test_define_sink_cross_product_accepts_with_name_checked_campaign_value
test_define_sink_cross_product_accepts_with_tuple_field_copy_checked_value
test_define_sink_cross_product_classifies_t2155_production_sinks_exactly
test_define_sink_cross_product_t2520_certify_entry_removal
test_define_sink_cross_product_t2520_opaque_closure_is_unresolved
test_define_sink_cross_product_t2520_local_fixed_shadow_is_unreachable
test_define_sink_cross_product_rejects_branch_local_returned_evidence
test_define_sink_cross_product_rejects_returned_evidence_after_sink
test_define_sink_cross_product_rejects_rebound_checked_name
test_define_sink_cross_product_rejects_loop_rebound_checked_name
test_define_sink_cross_product_rejects_unchecked_conditional_alias
test_define_sink_cross_product_rejects_short_circuit_returned_evidence
test_define_sink_cross_product_rejects_same_named_method_as_evidence
test_define_sink_cross_product_rejects_locally_defined_helper_shadow
test_define_sink_cross_product_rejects_helper_argument_shadow
test_define_sink_cross_product_rejects_default_walrus_rebinding
test_define_sink_cross_product_rejects_match_guard_walrus_rebinding
test_define_sink_cross_product_rejects_same_expression_walrus_rebinding
test_define_sink_cross_product_accepts_unrelated_nested_default
test_define_sink_cross_product_accepts_read_only_match_guard
test_define_sink_cross_product_rejects_class_global_helper_rebinding
test_define_sink_cross_product_rejects_called_nonlocal_checked_rebinding
test_define_sink_cross_product_rejects_star_import_after_helper_import
test_define_sink_cross_product_rejects_lambda_default_walrus_rebinding
test_define_sink_cross_product_rejects_false_guard_before_match_exit
test_define_sink_cross_product_rejects_false_guard_before_next_case
test_define_sink_cross_product_accepts_unrelated_global_and_nonlocal
test_define_sink_cross_product_marks_ungated_with_bindings_unresolved
test_define_sink_cross_product_marks_opaque_nonlexical_cell_unresolved
test_define_sink_cross_product_does_not_reuse_gate_for_another_macro
```

## 総括

赤2件とも修正・実走確認済みです。変更は許可された2ファイルの各1行のみ。production・分類件数の期待値は変更せず、commit 等の Git 操作も行っていません。