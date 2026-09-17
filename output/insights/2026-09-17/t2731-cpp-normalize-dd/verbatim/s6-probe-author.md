## 変更した file と差分

`orchestrator/tests/test_t2630_scan_boundary_reach.py` の `EVIDENCE_ROOT` のみ変更しました。

```diff
-    "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2630-scan-boundary-reach/evidence"
+    "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/evidence"
```

## collect-only の結果

指定コマンドで成功（終了コード0）：`4 tests collected in 2.38s`。実走はしていません。`git diff --check` も成功しました。

## 総括

指定の1箇所を変更済みです。既存の期待値・node・観測の意味は変更していません。commit・push・stash は未実施です。