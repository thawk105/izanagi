## 変更した箇所の diff

```diff
@@
     try:
         reports = []
+        output_tail_bytes = 4096
+
+        def _output_tail(output):
+            return (output or b"")[-output_tail_bytes:]
+
         for seed in ("1", "777"):
@@
-            reports.append(subprocess.run(
-                [sys.executable, "-c", script, trace_dir],
-                cwd=_REPO,
-                env=environment,
-                stdout=subprocess.PIPE,
-                stderr=subprocess.PIPE,
-                check=True,
-                timeout=30,
-            ).stdout)
+            try:
+                completed = subprocess.run(
+                    [sys.executable, "-c", script, trace_dir],
+                    cwd=_REPO,
+                    env=environment,
+                    stdout=subprocess.PIPE,
+                    stderr=subprocess.PIPE,
+                    check=False,
+                    timeout=120,
+                )
+            except subprocess.TimeoutExpired as exc:
+                assert False, (
+                    f"seed={seed} subprocess timed out after {exc.timeout}s; "
+                    f"stdout_tail={_output_tail(exc.stdout)!r}; "
+                    f"stderr_tail={_output_tail(exc.stderr)!r}"
+                )
+            assert completed.returncode == 0, (
+                f"seed={seed}; returncode={completed.returncode}; "
+                f"stdout_tail={_output_tail(completed.stdout)!r}; "
+                f"stderr_tail={_output_tail(completed.stderr)!r}"
+            )
+            reports.append(completed.stdout)
```

変更ファイルは `orchestrator/tests/test_verifier.py` だけです。`git diff --check` も成功しました。

## 実走した nodeid と結果

実行コマンド:

```text
PYTHONPATH=. python3 orchestrator/tests/test_verifier.py
```

対象 nodeid:

```text
orchestrator/tests/test_verifier.py::test_multi_ww_reason_report_is_hash_seed_deterministic
```

復元後の最終結果:

```text
PASS test_multi_ww_reason_report_is_hash_seed_deterministic
106 passed, 0 failed, 0 skipped
```

## 失敗時 message の確認

子の script に存在しない module の import を一時注入し、同じ自走 harness を実行しました。次の診断を確認しました。

```text
seed=1; returncode=1; stdout_tail=b''; stderr_tail=b'...ModuleNotFoundError: No module named \'definitely_missing_t2436_module\'...'
```

これにより seed、returncode、stdout 末尾、stderr 末尾が表示されることを確認しました。

確認後、一時 import は削除して元へ戻しました。検索で残存がないことを確認し、復元後の harness も 106 passed です。

## 残した assert の列挙

既存検査はすべて維持しています。

- 2 本の stdout の bytes 一致
- 辺 `0->1` の理由列が 6 key の WW 昇順
- `verdict == "non-serializable"`
- `serializable is False`
- `anomaly_count == 1`
- `total_cycles == 1`
- `phenomenon == "G2"`

`certified` を assert しないコメントも残しています。SHA-256 assert は追加せず、seed、key 数、trace、一時 trace の `finally` 削除も変更していません。

## 総括

指定された運用面の must-fix 2 件のみ修正し、最終状態で全 106 テストが成功しました。`git add` と `git commit` は実行していません。