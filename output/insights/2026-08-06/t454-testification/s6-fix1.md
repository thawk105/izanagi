## 総括

- 追加 node: `orchestrator/tests/test_mutation_harness.py::test_failed_nodes_strict_subset_never_counts_as_killed`
- 上記 node は `failed_keys == expected_keys` → `failed_keys <= expected_keys` を殺す。
- 追加 node: `orchestrator/tests/test_mutation_harness.py::test_same_test_part_from_different_path_never_counts_as_killed`
- 上記 node は `_match_key` が path 全体を捨て test part だけを返す変異を殺す。
- 実装済み・未実走。`pegasus02` のため pytest・変異走行は実施せず、緑は主張しない。
- `git diff --check` と一時領域への `py_compile` は成功。変更は指定テストファイルの 31 行追加だけ。

## 逐語 diff

```diff
diff --git a/orchestrator/tests/test_mutation_harness.py b/orchestrator/tests/test_mutation_harness.py
index be606681..4640db74 100644
--- a/orchestrator/tests/test_mutation_harness.py
+++ b/orchestrator/tests/test_mutation_harness.py
@@ -362,6 +362,37 @@ def test_failed_nodes_strict_superset_never_counts_as_killed(repo: Path) -> None
     assert status == "MISMATCH"
 
 
+def test_failed_nodes_strict_subset_never_counts_as_killed(repo: Path) -> None:
+    expected = [
+        "tests/test_gate.py::test_gate[one]",
+        "tests/test_gate.py::test_gate[two]",
+    ]
+    failed = ["tests/test_gate.py::test_gate[one]"]
+    status = MH._observed_status(
+        result={"timed_out": False, "rc": 1, "artifact_error": None},
+        failed=failed,
+        expected=expected,
+        repo=repo,
+    )
+
+    assert status == "MISMATCH"
+
+
+def test_same_test_part_from_different_path_never_counts_as_killed(
+    repo: Path,
+) -> None:
+    expected = ["tests/a.py::test_gate[one]"]
+    failed = ["tests/b.py::test_gate[one]"]
+    status = MH._observed_status(
+        result={"timed_out": False, "rc": 1, "artifact_error": None},
+        failed=failed,
+        expected=expected,
+        repo=repo,
+    )
+
+    assert status == "MISMATCH"
+
+
 @pytest.mark.parametrize("rc", [2, 3, 5])
 def test_abnormal_pytest_rc_never_counts_as_killed(repo: Path, rc: int) -> None:
     expected = ["tests/test_gate.py::test_gate[one]"]
```

## 残る穴

C-03/C-04 で指定された変異は静的には両方検出される。ただし未実走なので kill の実測確定は親に委ねる。

追加後も、path を完全には捨てず basename だけを残す弱化、たとえば `tests/x/a.py` と `tests/y/a.py` を同一視する `_match_key` は生存しうる。今回の C-04 入力は `a.py` と `b.py` で basename も異なるため、この部分的な path 弱化までは固定しない。

## 波及可能性

- production caller: `_apply_mutation` が同 seam を通常判定に使用する。[mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/tools/mutation_harness.py:1251)
- production caller: `_validate_mutation_record` が resume record の再検証に使用する。[mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/tools/mutation_harness.py:1518)
- 共有 fixture: 既存 `repo` fixture を引数として使うだけで、fixture 自体や生成 repo は変更していない。[test_mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:40)
- consumer test: ファイル単位の自走性を検査する meta-test があるが、対象ファイルには既存の `pytest.main([__file__])` がある。[test_plain_runner_coverage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_plain_runner_coverage.py:60)
- 新 node 名を直接参照する別 consumer は静的検索では見つからなかった。production・docs・既存期待値・repo fixture・受理集合は変更していない。