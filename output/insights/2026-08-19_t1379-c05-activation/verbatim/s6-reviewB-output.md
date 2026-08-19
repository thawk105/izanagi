## 総括

HEAD `2467033c` は裁定 v2 の範囲内の7ファイル בלבדです。§5 と `schedule.v1.json` は未変更で、現時点の must-fix はありません。`grep` の追加ヒットは ignored な `__pycache__` のみで、tracked な影響テストは [core]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1379-c05-activation/orchestrator/tests/test_s8c_preregistration_core.py)、[invariant](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1379-c05-activation/orchestrator/tests/test_s8c_preregistration_invariant.py)、[predicates](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1379-c05-activation/orchestrator/tests/test_s8c_preregistration_predicates.py) の3本です。

### must-fix（段9の land gate）

- **t1353 land 前に手動照合が必要。** `_negative_control_case`、`NON_MACHINE_CHECKABLE_NEGATIVE_CONTROL_CASES`、`test_satisfiable_predicate_requires_negative_control`、C05 bitflip test、C06件数期待が意味的に重なります（現行 [predicates.py:909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1379-c05-activation/orchestrator/tests/test_s8c_preregistration_predicates.py:909)、[predicates.py:991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1379-c05-activation/orchestrator/tests/test_s8c_preregistration_predicates.py:991)、[predicates.py:2471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1379-c05-activation/orchestrator/tests/test_s8c_preregistration_predicates.py:2471)、[predicates.py:2773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1379-c05-activation/orchestrator/tests/test_s8c_preregistration_predicates.py:2773)、[predicates.py:3083](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1379-c05-activation/orchestrator/tests/test_s8c_preregistration_predicates.py:3083)）。t1353側は C05 を旧 non-machine 集合に残し、件数を8としているため、land後は C03/C08 の static controls を保持しつつ、C05を machine集合へ残し、件数9・C05 reason・固定parametrizeを再確認すべきです。force/rebaseで迂回せず、衝突時は停止して再照準してください。

### nit

- s1 brief の [L7-L20](/home/SFC/tanab/.claude/jobs/caeb4545/tmp/dev-wave-t1379-c05-activation/s1-brief.md:7) と [L83-L85](/home/SFC/tanab/.claude/jobs/caeb4545/tmp/dev-wave-t1379-c05-activation/s1-brief.md:83) は裁定前の v4/g8・schedule込み・`UNSATISFIED` 想定です。s4 の scope外裁定と、現行の `schedule-schema-absent` は整合しているため、歴史記録として「裁定前」と明示するだけで、今回編集は不要です。

fixture は問題ありません。`repository_candidate_commit` は clean な統合HEADでも同一treeの synthetic child commitを作るだけで、実indexは汚しません。[current_commit_snapshot](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1379-c05-activation/orchestrator/tests/test_s8c_preregistration_predicates.py:145) も、未存在のschedule artifactをevidenceへ追加しないため統合後に壊れません。

C05契約反転、registry、v5、g9、固定hashは反映済みです。[g9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1379-c05-activation/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g9.json:1) の `supersedes_sha256` もg8のraw hashと一致します。pytestは指示どおり実走していません。