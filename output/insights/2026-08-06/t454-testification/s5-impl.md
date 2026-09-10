## 総括

- 追加 node: `test_failed_nodes_strict_superset_never_counts_as_killed`
- 純増: `expected ⊂ failed` を `"MISMATCH"` に固定。
- 既存被覆: 等集合の `"KILLED"` と互いに素な集合の `"MISMATCH"`。
- 実装済み・未実走。`pegasus02` のため pytest は実行せず、緑は主張しない。
- 変更はテスト 1 ファイル、13 行追加のみ。production・docs は不変。`git add`・commit 未実施。

## 変更前後

変更前の production は、正規化後の集合が等しい場合だけ `"KILLED"`、異なる場合は `"MISMATCH"` でした。[mutation_harness.py:1177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/tools/mutation_harness.py:1177)

ただし、テスト被覆は次の状態でした。

| 集合関係 | 現行挙動 | 変更前の被覆 | 変更後 |
|---|---|---|---|
| `expected == failed` | `KILLED` | 既存正例あり | 重複追加なし |
| `expected ∩ failed == ∅` | `MISMATCH` | 既存負例あり | 変更なし |
| `expected ⊂ failed` | `MISMATCH` | 専用 node なし | 新規追加 |
| `failed ⊂ expected` | `MISMATCH` | 専用 node は見つからず | 非 scope、追加なし |

変更後も production の受理・拒否挙動は不変です。新設 node により、`failed_keys == expected_keys` を `expected_keys <= failed_keys` に弱化すると赤になります。

## 追加した逐語 diff

```diff
+def test_failed_nodes_strict_superset_never_counts_as_killed(repo: Path) -> None:
+    expected = ["tests/test_gate.py::test_gate[one]"]
+    failed = [*expected, "tests/test_gate.py::test_gate[two]"]
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
```

追加位置は [test_mutation_harness.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:352) です。正規注入 seam `_observed_status` を直接呼び、monkeypatch は追加していません。

## 既存被覆の調査結果

- 等集合の正例は既存の  
  `orchestrator/tests/test_mutation_harness.py::test_normal_run_uses_cumulative_replacements_and_full_failed_line`  
  が、実失敗 node `test_gate[one]` と期待 node の一致、および `"KILLED"` を固定しています。[test_mutation_harness.py:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:205)

- 互いに素な集合は既存の  
  `orchestrator/tests/test_mutation_harness.py::test_parameter_suffix_is_matched_exactly`  
  が `expected={one}`, `failed={two}` の `"MISMATCH"` を固定しています。[test_mutation_harness.py:341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:341)

- 新設 test の名前そのものを列挙固定する meta-test は見つかりませんでした。ファイル単位では  
  `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`  
  が自走可能性を制約します。[test_plain_runner_coverage.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_plain_runner_coverage.py:60)  
  対象ファイルには既存の `pytest.main([__file__])` があります。[test_mutation_harness.py:1014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:1014)

## 検査と波及可能性

静的検査として `git diff --check` と Python の構文コンパイルを実行し、成功しました。pytest・変異テストは未実走です。

親が実走すべき範囲は次の 3 node です。

- 新設 strict-superset node
- 既存の等集合正例 node
- `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`

所有外への静的な波及面は次のとおりです。

- production caller: `_apply_mutation` が通常の変異結果判定で `_observed_status` を呼びます。[mutation_harness.py:1251](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/tools/mutation_harness.py:1251)
- production caller: `_validate_mutation_record` が resume ledger の再検証で同じ判定を呼びます。[mutation_harness.py:1518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/tools/mutation_harness.py:1518)
- 共有 fixture: 新設 node は既存 `repo` fixture を使用しますが、fixture や既存期待値は変更していません。[test_mutation_harness.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:39)
- consumer test: 新 node 名を直接参照する live consumer は検索上ありません。production 不変のため、既存 consumer の受理集合にも変更はありません。