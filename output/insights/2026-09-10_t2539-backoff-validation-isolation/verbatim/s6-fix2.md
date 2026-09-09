## 実装

- N1: [test_silo_validation_isolation.py:224](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix2/orchestrator/tests/test_silo_validation_isolation.py:224) で実体から `difflib` patch を生成し、[同:351](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix2/orchestrator/tests/test_silo_validation_isolation.py:351) で `TRACE` の closure reference／交差 4 件の symbol・depth を固定。
- N2: [同:322](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-fix2/orchestrator/tests/test_silo_validation_isolation.py:322) で rc=1、verdict、`ReadElement::get_tidword/1`・depth 1 を固定。必須引数不一致の ERROR 統制も維持。

## 実走結果

- Command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 orchestrator/tests/test_silo_validation_isolation.py`
- 20 nodes（19→20）、全緑、failures=0、rc=0。
- 追加: `test_cmake_trace_default_reports_macro_closure_intersections`
- 変更: `test_default_argument_callee_edit_is_not_reported_as_no_intersection`

## 変異への効き

- N1: M6 は macro reference と交差を 0 件にするため、4 件を要求する assertion が殺す。
- N2: M8 は既定引数呼出しを arity 不一致の ERROR にするため、rc=1 と交差 evidence の assertion が殺す。

## 総括

変更は指定されたテスト 1 file のみ。checker、docs、patches は未変更で、commit していません。