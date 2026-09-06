## 所見ごとの対応表

| 項目 | 状態 | 対応箇所 | test 関数 |
|---|---|---|---|
| D1 | closed | [job:175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/tools/pegasus/p3_s4_loop_pegasus.sh:175)、[job:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/tools/pegasus/p3_s4_loop_pegasus.sh:208)、[job:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/tools/pegasus/p3_s4_loop_pegasus.sh:339)、[test:724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/orchestrator/tests/test_p3_s4_loop_job_contract.py:724) | `test_superproject_status_failure_is_fail_closed` |
| D2 | closed | [job:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/tools/pegasus/p3_s4_loop_pegasus.sh:48)、[test:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/orchestrator/tests/test_p3_s4_loop_job_contract.py:177) | `test_job_body_static_contract` |
| D4 | closed | [job:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/tools/pegasus/p3_s4_loop_pegasus.sh:72)、[test:829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/orchestrator/tests/test_p3_s4_loop_job_contract.py:829) | `test_worktree_container_refuses_before_sentinels_or_artifacts` |
| D5 | closed | [job:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/tools/pegasus/p3_s4_loop_pegasus.sh:214)、[test:450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/orchestrator/tests/test_p3_s4_loop_job_contract.py:450) | `test_registered_fragment_mutants_have_one_static_failure` |
| D6 | closed | [test:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/orchestrator/tests/test_p3_s4_loop_job_contract.py:65)、[test:338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/orchestrator/tests/test_p3_s4_loop_job_contract.py:338) | `test_static_contract_orders_all_job_stages`、`test_dead_comment_cannot_mask_a_late_exit_trap` |
| D7 | closed | [test:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/orchestrator/tests/test_p3_s4_loop_job_contract.py:456)、[test:641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/orchestrator/tests/test_p3_s4_loop_job_contract.py:641) | `test_registered_fragment_mutants_have_one_static_failure`、`test_pbs_jobid_path_sanitization_is_load_bearing` |

## 実走結果

実行:

```text
PYTHONPATH=. python3 orchestrator/tests/test_p3_s4_loop_job_contract.py -q
```

結果: `44 passed in 1.72s`。範囲はファイル全体、`test_job_body_static_contract` から `test_job_body_has_valid_stdin_shell_syntax` までの全 44 nodeid です。`git diff --check` も通過しました。

## 所有外への波及

`rg` で未編集の参照先を確認しました。

- [tools/pegasus/README.md:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/tools/pegasus/README.md:32)
- [tools/pegasus/admission_registry.json:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/tools/pegasus/admission_registry.json:106)
- [docs/pegasus-runbook.md:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/docs/pegasus-runbook.md:508)
- [orchestrator/tests/test_hooks.py:2590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/orchestrator/tests/test_hooks.py:2590)
- [orchestrator/tests/test_acceptance_schedule_order.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/orchestrator/tests/test_acceptance_schedule_order.py:660) は全 test collection を動的に集計するため、追加 4 nodeid が波及します。D9 の対象なので未編集・未実走です。

既存の未追跡 `s6-adjudication.md` は変更していません。

## 総括

- D1・D2・D4・D5・D6・D7 はすべて closed です。
- `git status` の失敗を clean と扱う経路を 3 箇所とも fail-closed にしました。
- 指定された contract 自走は全 44 nodeid が緑です。
- 編集は指定された 2 ファイルだけで、commit・add・stash は行っていません。