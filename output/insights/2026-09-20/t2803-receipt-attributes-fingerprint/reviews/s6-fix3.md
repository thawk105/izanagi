## 総括

**実装済み・未実走。** `tools/check_ai_provenance.py` の2299行のコメントと2302〜2303行の argv 順序だけを変更しました。

変更後の呼び出し（逐語）：

```python
        paths = git_bytes("log", "--diff-merges=first-parent",
                          "--no-walk=unsorted", "--stdin", "--name-only", "-z",
                          "--format=", "--no-renames", input=merges)
```

指定 grep の結果（出現1件）：

```text
2302:        paths = git_bytes("log", "--diff-merges=first-parent",
```

`git diff --check` は成功。テスト・docs・probe は変更せず、commit は作成していません。

未完了は pytest による確認です。次の nodeid を `tools/run_tests.py` 経由で試行しましたが、`qstat -Q preflight rc=1` により終了（rc=16、`child_started=false`）。赤の解消は実走未確認です。

```text
orchestrator/tests/test_check_ai_provenance.py::test_path_batches_follow_correction_full_history_fallback
```