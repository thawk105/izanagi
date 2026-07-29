対応: **closed**

変更:

- [tools/run_tests.py:400](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/tools/run_tests.py:400) — `_NONSELECT_FLAGS` を acceptance の closed set として受理。`_is_full_suite` は未変更。
- [test_run_tests_preflight.py:151](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/orchestrator/tests/test_run_tests_preflight.py:151) — `--disable-warnings`／`-s` の acceptance 正例。
- [test_run_tests_preflight.py:200](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/orchestrator/tests/test_run_tests_preflight.py:200) — 未 stage 削除時 rc=13。
- [test_run_tests_preflight.py:206](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/orchestrator/tests/test_run_tests_preflight.py:206) — 削除なしで acceptance・削除検査・submodule preflight が rc=0。

実行 nodeid と結果:

- `test_acceptance_shape_positive_controls`
- `test_acceptance_shape_rejects_targeting_and_no_execution`
- `test_disable_warnings_keeps_unstaged_deletion_gate`
- `test_disable_warnings_passes_acceptance_preflights_without_deletion`

結果: **32 passed**

指定検証:

```text
python3 -m pytest orchestrator/tests/test_run_tests_preflight.py orchestrator/tests/test_run_tests_task_run.py orchestrator/tests/test_run_tests_nproc.py -q
135 passed in 1.47s
```

補助検査も `check_codex_agents.py`、`check_docs.py`、`git diff --check` すべて成功。docs 編集・commit は行っていません。

## 総括

新規 regression 1 件を closed。`--disable-warnings` 付き既定実行でも acceptance gate が維持され、`-o`／`-p`／`--override-ini` の拒否は維持されています。