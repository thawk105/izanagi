## 総括

**fix2 は実装済み・未実走です。** 変更は次の2ファイルのみです。

- [tools/check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2803-unit-impl/tools/check_ai_provenance.py:2269) の `_attribute_candidates`：指定の `git log` に変更。merge 0件では呼び出さず、hex 見出し除外を撤去。`--cc` 候補が第1親 diff に包含される根拠をコメントに記載。
- [orchestrator/tests/test_check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2803-unit-impl/orchestrator/tests/test_check_ai_provenance.py:8360) の `test_attribute_retired_directory_reintroduced_falls_back`：README だけを stage し、commit 前後で `.gitattributes` が未追跡であることを assert。他の assertion は維持。

base `f94b61fc8` の既存テスト関数は AST 比較で変更・削除0件。`test_path_batches_follow_receipt_final_selection` は無変更です。構文検査と `git diff --check` は成功しました。docs・probe・commit は変更していません。

次の2 nodeid を `tools/run_tests.py` 経由で試行しましたが、`qstat -Q preflight rc=1` により runner は rc=16、`child_started=false` で終了しました。

```text
orchestrator/tests/test_check_ai_provenance.py::test_attribute_retired_directory_reintroduced_falls_back
orchestrator/tests/test_check_ai_provenance.py::test_path_batches_follow_receipt_final_selection
```

未完了は pytest と変異の実走です。赤2件の解消は実走では未確認です。

指定 grep の `_attribute_candidates` 内の結果：

```text
2296:    merges = git_bytes("rev-list", "--merges", f"{policy}..{head}")
2297:    merges += git_bytes("rev-list", "--merges", "--no-walk", policy)
2299:    # git log --no-walk=unsorted --stdin --diff-merges=first-parent --name-only -z --format= --no-renames
2303:                          "--diff-merges=first-parent", "--name-only", "-z",
```

M-4 の exact 置換対象行（出現数1）：

```python
    for name in paths.split(b"\0"):
```

置換後：

```python
    for name in ():
```

M-1〜M-3 の対象行と EQ-1 の対象行は fix2 で変わらず、各出現数1です。

```python
        if source != {"kind": "absent"}:
```

```python
    return tuple(sorted(attribute_paths))
```