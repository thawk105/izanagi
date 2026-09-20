## 変更差分

```diff
diff --git a/orchestrator/tests/test_s8b_binding_driftguards.py b/orchestrator/tests/test_s8b_binding_driftguards.py
index d03998f09..2afd0661d 100644
--- a/orchestrator/tests/test_s8b_binding_driftguards.py
+++ b/orchestrator/tests/test_s8b_binding_driftguards.py
@@ -345,7 +345,7 @@ def test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal_in_tm
         )
 
     assert decision.allowed is False
-    assert len(decision.refusals) == 2, decision.refusals
+    assert len(decision.refusals) == 3, decision.refusals
     assert any(
         refusal.startswith("manifest-verify:")
         and "binding_identity entry schema が不一致" in refusal
@@ -355,6 +355,11 @@ def test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal_in_tm
         refusal.startswith("freeze-ratify: [no-active]")
         for refusal in decision.refusals
     ), decision.refusals
+    # tmp root に known axes source が無い fixture 由来の拒否も standalone core が freeze / known axes / manifest と集約する。
+    assert any(
+        refusal.startswith("known-axes-freeze-verify:")
+        for refusal in decision.refusals
+    ), decision.refusals
 
 
 def test_run_block_broken_binding_manifest_aggregates_refusals_in_tmp_repo(tmp_path):
```

## 未実走・限界

`python3 -m py_compile orchestrator/tests/test_s8b_binding_driftguards.py` は成功しました。pytest は未実走で、親の dispatch に委ねます。

## 総括

指定の追加テストだけを修正し、実測の3件と各 prefix、binding schema 不一致を要求しました。他テスト・production は未変更。add・commit・push はしていません。