## 総括
- 実装済み・未実走。Pegasus login node のため pytest・変異 matrix は実行しておらず、緑は主張しない。
- `orchestrator/tests/test_mutation_harness.py::test_match_key_keeps_distinct_pytest_nodes_separate[basename]` — (1) basename 化を検出。
- `orchestrator/tests/test_mutation_harness.py::test_match_key_keeps_distinct_pytest_nodes_separate[tail2]` — (2) 末尾 2 component 化を検出。
- `orchestrator/tests/test_mutation_harness.py::test_match_key_keeps_distinct_pytest_nodes_separate[casefold]` — (3) casefold 化を検出。
- `orchestrator/tests/test_mutation_harness.py::test_match_key_keeps_distinct_pytest_nodes_separate[classns]` — (4) class namespace 除去を検出。
- 全ケースは `rc=1`、expected/failed 各 1 node で `"MISMATCH"` を要求する。
- `git diff --check` は rc=0。変更は指定テストファイルへの 34 行追加だけで、commit はしていない。

### 逐語 diff

```diff
diff --git a/orchestrator/tests/test_mutation_harness.py b/orchestrator/tests/test_mutation_harness.py
index 4640db74..ad6c6382 100644
--- a/orchestrator/tests/test_mutation_harness.py
+++ b/orchestrator/tests/test_mutation_harness.py
@@ -393,6 +393,40 @@ def test_same_test_part_from_different_path_never_counts_as_killed(
     assert status == "MISMATCH"
 
 
+@pytest.mark.parametrize(
+    ("expected_node", "failed_node"),
+    [
+        pytest.param(
+            "tests/x/a.py::test_gate", "tests/y/a.py::test_gate", id="basename"
+        ),
+        pytest.param(
+            "tests/p/x/a.py::test_gate",
+            "tests/q/x/a.py::test_gate",
+            id="tail2",
+        ),
+        pytest.param(
+            "tests/A.py::test_gate", "tests/a.py::test_gate", id="casefold"
+        ),
+        pytest.param(
+            "tests/a.py::C1::test_gate",
+            "tests/a.py::C2::test_gate",
+            id="classns",
+        ),
+    ],
+)
+def test_match_key_keeps_distinct_pytest_nodes_separate(
+    repo: Path, expected_node: str, failed_node: str
+) -> None:
+    status = MH._observed_status(
+        result={"timed_out": False, "rc": 1, "artifact_error": None},
+        failed=[failed_node],
+        expected=[expected_node],
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

### 受理形式の確認

[`_normalize_node`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/tools/mutation_harness.py:798) は最初の `::` だけで分割し、残りの test part を保持します。そのため `tests/a.py::C1::test_gate` も `C1::test_gate` を失わず受理されます。4 ケースの path はすべて `_safe_relpath` の POSIX 相対 path 条件を満たします。

### 残る穴

指定された4弱化変異について、静的に生存するものはありません。ただし未実走なので、実際の KILLED 判定は親による変異 matrix 再走が必要です。列挙外の任意の identity-loss 変異まで完全に被覆したとは主張しません。

### 波及可能性

- 所有外 caller: `_observed_status` は [`_apply_mutation`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/tools/mutation_harness.py:1251) と [`_validate_mutation_record`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/tools/mutation_harness.py:1518) から呼ばれます。production は未変更ですが、将来の key 弱化を両経路の台帳 status に届く前に検出します。
- 共有 fixture: [`repo`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:39) は変更していません。新テスト自身は `monkeypatch` を要求・操作せず、repo 内容も書き換えません。
- consumer test: KILLED 正例を固定する [`test_normal_run_uses_cumulative_replacements_and_full_failed_line`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:205) や resume 台帳検証にはコード上の変更はありません。変異時には新4 node が期待される検出 node になります。