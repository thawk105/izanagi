## 変更

[test_official_perf_closure.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/tests/test_official_perf_closure.py:61) の `_REVIEWED_PERF_FILES` に新 driver と指定の注記を追加しました。別の登録簿や期待値は変更していません。commit はしていません。

## 確認の実走

`py_compile` 成功、test file の直接実行は **7 passed, 0 failed**。`check_codex_agents.py`、`check_docs.py`、`git diff --check` も成功しました。pytest は実行していません。

## 総括

H1 の登録漏れを修正し、変更は指定された 1 ファイルだけです。