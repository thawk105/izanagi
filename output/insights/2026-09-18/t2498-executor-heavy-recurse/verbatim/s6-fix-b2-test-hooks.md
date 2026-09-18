## 追加したテスト (node id 一覧)

- `orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_deep_nesting_has_no_stack_limit`
- `orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_precedes_sanctioned_allow`
- `orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_matches_direct_form`

## 実測 (直接呼び出し、現行での挙動)

`compile()` と `git diff --check` は成功。探索パスを補って module を import し、3関数を直接呼び出しました。

| 関数名の末尾 | 結果 |
|---|---|
| `deep_nesting_has_no_stack_limit` | 1入力目で `RecursionError`。残り2入力は未到達 |
| `precedes_sanctioned_allow` | 成功（2入力） |
| `matches_direct_form` | 成功（7組） |

すべて fix A2 前の想定どおりです。pytest は実行していません。

## 総括

指定位置に3関数、47行を追加しました。変更は `test_hooks.py` のみで、既存テストは変更していません。fixture・xfail・skip の追加、`git add`・`git commit` は行っていません。