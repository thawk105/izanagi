## 総括

- **FIX-6:** catch-all を checkpoint 読取・decode・schema 由来の例外に限定し、`AttributeError` が再分類されない負例を追加。
- **FIX-7:** `0` の下限 gate と `1.0` の非 `int` gate を独立 node に分離。production の型検査は変更なし。
- **編集箇所:** [p3_autonomous_workload_trial.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:196)、[test_p3_autonomous_workload_trial.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:112)、[同 AttributeError 負例](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:432)。
- **nodeid:**
  - 旧 `test_generation_budget_rejects_zero_and_non_int[0]` → `test_generation_budget_rejects_below_minimum`
  - 旧 `test_generation_budget_rejects_zero_and_non_int[1.0]` → `test_generation_budget_rejects_non_int_float`
  - 新設 `test_freshness_does_not_reclassify_attribute_error`
  - bool・`int` サブクラス・既存 freshness 2 node は変更なし。
- **列挙した例外型:** 捕捉対象は `OSError`、`ValueError`（`json.JSONDecodeError`、`UnicodeDecodeError`、`WhiteboardLeakError`を包含）、`KeyError`、`OverflowError`。`AttributeError`、`TypeError`、`AssertionError` は素通し。
- **検査結果:** `python3 tools/run_tests.py orchestrator/tests/test_p3_autonomous_workload_trial.py -rf` は Pegasus dispatch の `qstat -Q preflight rc=1`、終了コード16で pytest 未実行。緑は主張しない。`git diff --check`、`py_compile`、`check_codex_agents.py`、`check_docs.py` はすべて rc=0。
- **所有外への波及可能性:** 旧 parametrize node を参照する親所有の変異 matrix/harness は新 nodeid への更新が必要。docs、A-02、FIX-1・2・4・5、role/adapters は未編集。commit・stage 操作も未実施。