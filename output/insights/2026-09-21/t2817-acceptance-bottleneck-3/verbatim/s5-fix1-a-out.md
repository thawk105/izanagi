## 変更した内容 (diff の逐語)

```diff
diff --git a/tools/t2817_probe_plugin.py b/tools/t2817_probe_plugin.py
index e4a1487b8..6ba1ba05a 100644
--- a/tools/t2817_probe_plugin.py
+++ b/tools/t2817_probe_plugin.py
@@ -28,11 +28,13 @@ def worker(config):


 def facts(config):
-    return {
+    ledger = getattr(config, "_izanagi_acceptance_duration_seconds_by_nodeid", None)
+    result = {
         **{key: getattr(config.option, key, None) for key in
            ("dist", "loadscopereorder", "numprocesses", "maxfail")},
         "shard_spec": getattr(config, "_izanagi_acceptance_shard_spec", None) is not None,
         "ledger_attr": hasattr(config, "_izanagi_acceptance_duration_seconds_by_nodeid"),
+        "ledger_entries": len(ledger) if isinstance(ledger, dict) else None,
         "early_memo_attr": hasattr(config, "_izanagi_early_memo_job"),
         "effective_scheduler_attr": hasattr(config, "_izanagi_effective_scheduler"),
         "argv": list(sys.argv),
@@ -40,6 +42,41 @@ def facts(config):
                 k.startswith(("IZANAGI_", "PYTEST_", "T2817_")) or
                 k in ("PYTHONDONTWRITEBYTECODE", "TMPDIR")},
     }
+    if worker(config):
+        workerinput = config.workerinput
+        ledger_key = "izanagi_acceptance_duration_ledger_v1"
+        payload = workerinput.get(ledger_key)
+        result.update(
+            workerinput_keys=sorted(workerinput.keys()),
+            ledger_payload_present=ledger_key in workerinput,
+            ledger_payload_entries=(
+                len(payload) if isinstance(payload, (dict, list)) else None),
+            early_memo_paths_present="izanagi_early_memo_paths" in workerinput,
+        )
+    else:
+        # Mirror conftest's parsed-option gate without importing repository code.
+        disabled_booleans = (
+            "stepwise", "stepwise_skip", "stepwise_reset", "failedfirst",
+            "newfirst", "lf", "collectonly", "setuponly", "setupplan",
+            "showfixtures", "show_fixtures_per_test", "trace",
+        )
+        option = config.option
+        inputs = {
+            "dist": getattr(option, "dist", None),
+            "maxfail": getattr(option, "maxfail", 0),
+            "loadscopereorder": getattr(option, "loadscopereorder", True),
+            "cacheshow": getattr(option, "cacheshow", None),
+            **{name: getattr(option, name, False) for name in disabled_booleans},
+        }
+        result["ledger_option_inputs"] = inputs
+        result["ledger_should_load"] = (
+            inputs["dist"] == "loadgroup"
+            and inputs["maxfail"] in (None, 0)
+            and not any(bool(inputs[name]) for name in disabled_booleans)
+            and inputs["cacheshow"] is None
+            and inputs["loadscopereorder"] is not False
+        )
+    return result


 def write(config):
```

worker 側の追加項目は、既存経路で `config.workeroutput["t2817"]["config"]` に入ります。

## 実走した検査

以下はいずれも rc=0。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/t2817-fix1-pycompile python3.10 -m py_compile tools/t2817_probe_plugin.py
```

出力なし。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/t2817-fix1-pycompile PYTHONPATH="$PWD/tools" python3.10 -c 'import t2817_probe_plugin; print("plugin import: OK")'
```

```text
plugin import: OK
```

pytest は起動していません。

## 所有外への波及

`git status --porcelain` の出力：

```text
 M tools/t2817_probe_plugin.py
```

所有外への変更は無し。集計器・conftest・テスト・docs は未変更です。deselect・skip・hold・verifier に触れていません。`git add`／`git commit` は実行していません。

## 総括

指定の記録項目を実装し、構文・import 検査は通過しました。S2／S3 の実際の JSON 出力と worker 配送の確認は、親による再実走が必要です。